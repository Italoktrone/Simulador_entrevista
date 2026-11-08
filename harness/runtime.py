"""Control de entrevistas con historial íntegro y memoria opcional, sin consola."""

from time import perf_counter

from harness.interview_config import InterviewSetup
from harness.llm.client import LLMClient, LLMError, LLMInvalidResponseError, LLMResponse
from harness.history_summary import HistorySummaryError, generate_summary
from harness.live_context import LiveContextPolicy, audit_preparation, selector_metrics
from harness.llm.messages import ChatMessage
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import PromptBuildError, build_messages
from harness.session_state import SessionState, describe_issue
from harness.summary_context import prepare_summary_context
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.intervention_log import classification_configuration, select_classification_context
from harness.response_policy import ResponsePolicyDecision, decide_response
from harness.response_validator import ResponseValidationError, validate_support_claims
from harness.behavioral_evidence import select_support_evidence, audit_support_selection


class InterviewFinishedError(RuntimeError):
    """La ejecución se cerró o alcanzó su límite de preguntas."""


class InterviewRuntime:
    """Escenario fijo, contador y turnos completos en memoria por ejecución."""

    def __init__(
        self, setup: InterviewSetup, instructions: str, client: LLMClient,
        *, provider: str | None = None, model: str | None = None,
        context_policy: LiveContextPolicy | None = None,
        classifier: HybridQuestionClassifier | None = None,
        classification_info: dict | None = None,
        evaluator=None,
    ) -> None:
        if not isinstance(instructions, str) or not instructions.strip():
            raise PromptBuildError("Las instrucciones deben ser texto no vacío.")
        self._setup = setup
        self._instructions = instructions
        self._client = client
        self._session = SessionState(setup, instructions, provider=provider, model=model)
        if context_policy is not None and not isinstance(context_policy, LiveContextPolicy):
            raise ValueError("context_policy debe ser LiveContextPolicy o None.")
        self._context_policy = context_policy
        self._context_active = False
        if context_policy is not None:
            self._session.enable_context_policy(context_policy.to_dict())
        if classifier is not None and not isinstance(classifier, HybridQuestionClassifier):
            raise ValueError("classifier debe ser HybridQuestionClassifier o None.")
        if classifier is None and classification_info is not None:
            raise ValueError("Los datos del clasificador requieren un clasificador activo.")
        self._classifier = classifier
        if classifier is not None:
            self._session.enable_classification(classification_configuration(classification_info))
        if evaluator is not None:
            from harness.question_evaluator import QuestionEvaluator
            if not isinstance(evaluator, QuestionEvaluator) or classifier is None:
                raise ValueError("El evaluador requiere QuestionEvaluator y clasificación activa.")
            self._session.enable_evaluation(evaluator.rubric)
        self._evaluator = evaluator
        self._last_behavioral_selection = None

    @property
    def last_behavioral_selection(self):
        return audit_support_selection(self._last_behavioral_selection)

    @property
    def evaluation_enabled(self) -> bool:
        return self._evaluator is not None

    @property
    def last_evaluation(self):
        records = self.session_dict().get("evaluations", [])
        return records[-1] if records else None

    @property
    def classification_enabled(self) -> bool:
        return self._classifier is not None

    @property
    def setup(self) -> InterviewSetup:
        return self._setup

    @property
    def max_questions(self) -> int:
        return self._session.max_questions

    @property
    def questions_asked(self) -> int:
        return self._session.questions_asked

    @property
    def session_id(self) -> str:
        return self._session.session_id

    @property
    def finished(self) -> bool:
        return self._session.is_closed or self.questions_asked >= self.max_questions

    def close(self, reason: str = "closed") -> None:
        self._session.close(reason)

    def session_dict(self) -> dict:
        """Copia del registro técnico completo; no se envía al modelo."""
        return self._session.snapshot()

    def history_messages(self) -> list[ChatMessage]:
        """Copia de la conversación aceptada; no son hechos validados del perfil."""
        return self._session.history_messages()

    def assert_source_unchanged(self) -> None:
        try:
            self._setup.candidate.assert_source_unchanged()
        except ProfileIntegrityError as error:
            self._session.mark_source_integrity(False)
            if not self._session.has_pending_attempt and not self._session.has_issue("profile_integrity_error"):
                self._session.record_issue(error)
            self.close("profile_integrity_error")
            raise
        else:
            self._session.mark_source_integrity(True)

    def _prepare_live_context(self, question: str, candidate_metadata: dict | None = None) -> tuple[list[ChatMessage], dict]:
        started = perf_counter()
        snapshot = self.session_dict()
        policy = self._context_policy
        full_summary, _ = generate_summary(snapshot, None, keep_recent_pairs=20)
        full = prepare_summary_context(self._setup, question, instructions=self._instructions, session=snapshot,
                                       summary=full_summary, candidate_metadata=candidate_metadata)
        reason = policy.reason(snapshot, self._context_active)
        event = {"before_question_number": self.questions_asked + 1, "candidate_sent": False,
                 "trigger_reason": reason, "selector_status": "not_requested", "preparation": None,
                 "summary_selections": None, "selector_metrics": None, "issues": []}
        prepared = full
        if reason not in {"insufficient_history", "below_threshold"}:
            self._context_active = True
            try:
                try:
                    summary, response = generate_summary(snapshot, self._client, keep_recent_pairs=policy.keep_recent_pairs)
                    event.update(selector_status="completed", summary_selections=summary["selections"], selector_metrics=selector_metrics(response))
                except BaseException as error:
                    event["issues"].append(describe_issue(error))
                    raise
                finally:
                    self.assert_source_unchanged()
                prepared = prepare_summary_context(self._setup, question, instructions=self._instructions, session=snapshot,
                                                   summary=summary, candidate_metadata=candidate_metadata)
            except (ProfileIntegrityError, KeyboardInterrupt) as error:
                event["selector_status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "aborted"
                if isinstance(error, KeyboardInterrupt) and not event["issues"]:
                    event["issues"].append(describe_issue(error))
                # La integridad ya se registra en el nivel de sesión por el guardián.
                event["preparation_elapsed_seconds"] = perf_counter() - started
                self._session.record_context_event(event)
                raise
            except (HistorySummaryError, LLMError) as error:
                event.update(selector_status="failed", summary_selections=None)
                if not event["issues"]:
                    event["issues"].append(describe_issue(error))
                prepared = full
                prepared["reason"] = "selector_failed"
            except BaseException as error:
                event["selector_status"] = "aborted"
                if not event["issues"]:
                    event["issues"].append(describe_issue(error))
                event["preparation_elapsed_seconds"] = perf_counter() - started
                self._session.record_context_event(event)
                raise
        event["preparation"] = audit_preparation(prepared)
        event["preparation_elapsed_seconds"] = perf_counter() - started
        return prepared["messages"], event

    def ask(self, question: str, *, on_candidate_response=None) -> LLMResponse | ResponsePolicyDecision:
        """Clasificar primero si está activo; solo los envíos al candidato cuentan."""
        self._last_behavioral_selection = None
        if self.finished:
            raise InterviewFinishedError("La entrevista ya finalizó o alcanzó su límite.")
        if self._classifier is None:
            return self._ask_candidate(question)
        self.assert_source_unchanged()
        context = select_classification_context(self.session_dict()["attempts"])
        ids = tuple(turn["turn_number"] for turn in context)
        # Validar el tipo antes de crear una intervención evita registros sin texto.
        if not isinstance(question, str):
            raise PromptBuildError("La intervención debe ser texto.")
        number = self._session.begin_intervention(question, list(ids))
        identifier = f"{self.session_id}:i{number}"
        evaluation_request = None
        if self._evaluator is not None:
            evaluation_request = self._evaluator.make_request(
                question=question, configuration=self._setup.config_dict(), job=self._setup.job_dict(),
                attempts=self.session_dict()["attempts"], classification=None)
        try:
            try:
                report = self._classifier.classify(
                    question, intervention_id=identifier, configuration=self._setup.config_dict(),
                    context_turns=context, competency=None,
                )
            finally:
                self.assert_source_unchanged()
            decision = decide_response(report.result, expected_intervention_id=identifier,
                                       expected_text=question, allowed_context_turn_ids=ids)
            self._session.record_classification(number, report.to_dict(), decision.to_dict())
            if self._evaluator is not None:
                evaluation_request = self._evaluator.make_request(
                    question=question, configuration=self._setup.config_dict(), job=self._setup.job_dict(),
                    attempts=self.session_dict()["attempts"], classification=report.result,
                )
            if decision.action != "responder":
                if self._evaluator is not None:
                    self._session.record_evaluation(self._evaluator.skipped(
                        evaluation_request, session_id=self.session_id, intervention_id=identifier, action=decision.action))
                self._session.finish_intervention(number, status="handled", issues=[])
                return decision
            response = self._ask_candidate(question, candidate_metadata=decision.candidate_metadata,
                                           intervention_number=number)
            if self._evaluator is not None:
                if on_candidate_response is not None:
                    on_candidate_response(response)
                try:
                    record = self._evaluator.evaluate(evaluation_request, session_id=self.session_id,
                                                      intervention_id=identifier, question_number=self.questions_asked)
                except Exception:
                    record = self._evaluator.unavailable(evaluation_request, session_id=self.session_id,
                                                         intervention_id=identifier, question_number=self.questions_asked)
                self._session.record_evaluation(record)
        except BaseException as error:
            event = self.session_dict()["interventions"][-1]
            sent = event["candidate_question_number"]
            if sent is not None:
                attempt = self.session_dict()["attempts"][sent - 1]
                status, issues = attempt["status"], attempt["issues"]
            else:
                status = "interrupted" if isinstance(error, KeyboardInterrupt) else "error"
                issues = [describe_issue(error)]
            if self._evaluator is not None and evaluation_request is not None:
                existing = self.session_dict()["evaluations"]
                if not any(e["intervention_id"] == identifier for e in existing):
                    self._session.record_evaluation(self._evaluator.skipped(
                        evaluation_request, session_id=self.session_id, intervention_id=identifier,
                        question_number=sent, action="interrupted" if isinstance(error, KeyboardInterrupt) else "candidate_error" if sent is not None else "error_tecnico"))
            self._session.finish_intervention(number, status=status, issues=issues)
            raise
        self._session.finish_intervention(number, status="completed", issues=[])
        return response

    def _ask_candidate(self, question: str, *, candidate_metadata: dict | None = None,
                       intervention_number: int | None = None) -> LLMResponse:
        """Una pregunta válida enviada consume un lugar, incluso si el LLM falla."""

        if self.finished:
            raise InterviewFinishedError("La entrevista ya finalizó o alcanzó su límite.")
        messages = build_messages(
            self._setup, question, instructions=self._instructions, history=self.history_messages(),
            candidate_metadata=candidate_metadata,
        )
        self._last_behavioral_selection = select_support_evidence(self._setup.candidate.to_dict(), question, self.history_messages())
        self.assert_source_unchanged()
        context_event = None
        if self._context_policy is not None:
            messages, context_event = self._prepare_live_context(question, candidate_metadata)
        number = self._session.begin_attempt(question)
        if intervention_number is not None:
            self._session.link_candidate_attempt(intervention_number, number)
        if context_event is not None:
            context_event["candidate_sent"] = True
            self._session.record_context_event(context_event)
        response = None
        generation_issue = None
        error_status = "error"
        try:
            try:
                response = self._client.generate(messages)
                validate_support_claims(response, self._last_behavioral_selection)
            except BaseException as error:
                if isinstance(error, ResponseValidationError):
                    response = error.response
                generation_issue = describe_issue(error)
                raise
            finally:
                self.assert_source_unchanged()
            if response.finish_reason == "length":
                error_status = "incomplete"
                raise LLMInvalidResponseError(
                    "La respuesta alcanzó el límite de salida y quedó incompleta; no se mostrará como respuesta del candidato."
                )
        except BaseException as error:
            issue = describe_issue(error)
            issues = [generation_issue] if generation_issue is not None else []
            if issue not in issues:
                issues.append(issue)
            status = "interrupted" if isinstance(error, KeyboardInterrupt) else error_status
            self._session.finish_attempt(number, status=status, response=response, issues=issues)
            if self.questions_asked >= self.max_questions:
                self.close("interrupted" if status == "interrupted" else "question_limit")
            raise
        self._session.finish_attempt(number, status="completed", response=response, issues=[])
        if self.questions_asked >= self.max_questions:
            self.close("question_limit")
        return response

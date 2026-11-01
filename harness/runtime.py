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


class InterviewFinishedError(RuntimeError):
    """La ejecución se cerró o alcanzó su límite de preguntas."""


class InterviewRuntime:
    """Escenario fijo, contador y turnos completos en memoria por ejecución."""

    def __init__(
        self, setup: InterviewSetup, instructions: str, client: LLMClient,
        *, provider: str | None = None, model: str | None = None,
        context_policy: LiveContextPolicy | None = None,
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

    def _prepare_live_context(self, question: str) -> tuple[list[ChatMessage], dict]:
        started = perf_counter()
        snapshot = self.session_dict()
        policy = self._context_policy
        full_summary, _ = generate_summary(snapshot, None, keep_recent_pairs=20)
        full = prepare_summary_context(self._setup, question, instructions=self._instructions, session=snapshot, summary=full_summary)
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
                prepared = prepare_summary_context(self._setup, question, instructions=self._instructions, session=snapshot, summary=summary)
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

    def ask(self, question: str) -> LLMResponse:
        """Una pregunta válida enviada consume un lugar, incluso si el LLM falla."""

        if self.finished:
            raise InterviewFinishedError("La entrevista ya finalizó o alcanzó su límite.")
        messages = build_messages(
            self._setup, question, instructions=self._instructions, history=self.history_messages()
        )
        self.assert_source_unchanged()
        context_event = None
        if self._context_policy is not None:
            messages, context_event = self._prepare_live_context(question)
        number = self._session.begin_attempt(question)
        if context_event is not None:
            context_event["candidate_sent"] = True
            self._session.record_context_event(context_event)
        response = None
        generation_issue = None
        error_status = "error"
        try:
            try:
                response = self._client.generate(messages)
            except BaseException as error:
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

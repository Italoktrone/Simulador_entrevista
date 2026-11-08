"""Sesiones del arnés, exclusión por turno, reintentos y auditoría JSONL."""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from threading import Lock

from app.contracts import RunOutput
from harness.document_search import DocumentSearch, GroundedClient
from harness.candidate_catalog import CANDIDATES, load_candidate_setup
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.llm.client import LLMError
from harness.llm.factory import create_client
from harness.llm_question_classifier import LLMQuestionClassifier, create_classification_client
from harness.prompt_builder import load_instructions
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.response_policy import ResponsePolicyDecision
from harness.runtime import InterviewRuntime
from harness.scoring import load_rubric
from harness.session_log import save_session


ROOT = Path(__file__).resolve().parents[1]


class ServiceError(Exception):
    def __init__(self, status: int, code: str):
        self.status = status
        self.code = code
        super().__init__(code)


@contextmanager
def runtime_session(options):
    setup = load_candidate_setup(options.candidate_id)
    with ExitStack() as resources:
        client = resources.enter_context(create_client())
        grounded = GroundedClient(client)
        settings = {"provider": client.provider, "model": client.settings.model}
        if options.classify or options.evaluate:
            classifier_client = resources.enter_context(create_classification_client())
            settings.update(
                classifier=HybridQuestionClassifier(LLMQuestionClassifier(classifier_client)),
                classification_info={"requested_provider": classifier_client.provider,
                                     "requested_model": classifier_client.settings.model,
                                     "max_output_tokens": classifier_client.settings.max_output_tokens},
            )
        if options.evaluate:
            rubric = load_rubric()
            evaluator = resources.enter_context(create_evaluation_client(rubric=rubric))
            settings["evaluator"] = QuestionEvaluator(evaluator, rubric=rubric)
        yield InterviewRuntime(setup, load_instructions(), grounded, **settings), grounded


@dataclass
class Session:
    runtime: InterviewRuntime
    grounded: GroundedClient
    resources: object
    lock: object = field(default_factory=Lock)
    requests: dict = field(default_factory=dict)
    saved: bool = False
    released: bool = False


@dataclass
class RunRecord:
    signature: str
    result: dict
    logged: bool = False
    behavioral_selection: dict | None = None


class InterviewService:
    def __init__(self, directory: Path, factory=runtime_session, max_sessions=100):
        self.directory = directory
        self.factory = factory
        self.max_sessions = max_sessions
        self.sessions = {}
        self.starts = {}
        self.lock = Lock()
        self.log_lock = Lock()

    def log(self, session_id, request_id, event, **fields):
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "session_id": session_id,
                  "run_id": request_id, "event": event, **fields}
        path = self.directory / "logs" / f"{session_id}.jsonl"
        encoded = (json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        with self.log_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("ab") as stream:
                position = stream.tell()
                try:
                    if stream.write(encoded) != len(encoded):
                        raise OSError("Escritura de auditoría incompleta.")
                    stream.flush()
                    os.fsync(stream.fileno())
                except OSError:
                    stream.seek(position)
                    stream.truncate()
                    raise

    def start(self, options):
        request_id = str(options.request_id)
        signature = options.model_dump_json()
        if options.candidate_id not in CANDIDATES:
            raise ServiceError(404, "candidate_not_found")
        with self.lock:
            if request_id in self.starts:
                previous, session_id = self.starts[request_id]
                if signature != previous:
                    raise ServiceError(409, "request_conflict")
                return self.public(self.sessions[session_id])
            if len(self.sessions) >= self.max_sessions:
                raise ServiceError(503, "session_capacity")
            resources = self.factory(options)
            try:
                runtime, grounded = resources.__enter__()
                if runtime.setup.candidate.candidate_id != options.candidate_id:
                    raise ServiceError(500, "candidate_mismatch")
                session = Session(runtime, grounded, resources)
                identifier = runtime.session_id
                self.log(identifier, request_id, "session_started")
            except BaseException:
                resources.__exit__(*sys.exc_info())
                raise
            self.sessions[identifier] = session
            self.starts[request_id] = (signature, identifier)
            return self.public(session)

    def get(self, identifier):
        with self.lock:
            session = self.sessions.get(str(identifier))
        if session is None:
            raise ServiceError(404, "session_not_found")
        return session

    @contextmanager
    def exclusive(self, identifier):
        session = self.get(identifier)
        if not session.lock.acquire(blocking=False):
            raise ServiceError(409, "session_busy")
        try:
            yield session
        finally:
            session.lock.release()

    def public(self, session):
        runtime = session.runtime
        data = runtime.session_dict()
        return {"session_id": runtime.session_id, "status": data["status"],
                "candidate_id": runtime.setup.candidate.candidate_id,
                "questions_asked": runtime.questions_asked, "max_questions": runtime.max_questions,
                "classify": runtime.classification_enabled, "evaluate": runtime.evaluation_enabled,
                "resume": runtime.setup.candidate.to_public_resume(), "job": runtime.setup.job_dict(),
                "turns": [record.result for record in session.requests.values()]}

    def finish(self, session):
        if not session.saved:
            session.runtime.assert_source_unchanged()
            save_session(session.runtime.session_dict(), self.directory / "sessions")
            session.saved = True
        if not session.released:
            session.resources.__exit__(None, None, None)
            session.released = True

    def run(self, payload):
        with self.exclusive(payload.session_id) as session:
            identifier = str(payload.request_id)
            signature = payload.model_dump_json()
            if identifier in session.requests:
                record = session.requests[identifier]
                if signature != record.signature:
                    raise ServiceError(409, "request_conflict")
                return self.publish(session, identifier, record)
            runtime = session.runtime
            if runtime.finished:
                raise ServiceError(409, "session_closed")
            session.grounded.sources = DocumentSearch.from_setup(runtime.setup).search(payload.question) if payload.use_rag else []
            self.log(runtime.session_id, identifier, "run_started",
                     question_sha256=hashlib.sha256(payload.question.encode("utf-8")).hexdigest())
            reply, status, action, error_code = None, "error", "error_tecnico", None
            try:
                response = runtime.ask(payload.question)
                if isinstance(response, ResponsePolicyDecision):
                    reply, action = response.text, response.action
                    status = "error" if action == "error_tecnico" else "handled"
                    error_code = response.code if status == "error" else None
                else:
                    reply, status, action = response.text, "completed", "responder"
            except LLMError:
                error_code = "model_error"
            except Exception:
                # Un error inesperado detiene la sesión para conservar su estado.
                runtime.close("interrupted")
                error_code = "execution_error"
            result = RunOutput(
                session_id=payload.session_id, request_id=payload.request_id, status=status,
                reply=reply, action=action, questions_asked=runtime.questions_asked,
                max_questions=runtime.max_questions, closed=runtime.finished,
                sources=session.grounded.sources,
                evaluation=None if status == "error" else runtime.last_evaluation, error_code=error_code,
            ).model_dump(mode="json")
            record = RunRecord(signature, result, behavioral_selection=runtime.last_behavioral_selection)
            session.requests[identifier] = record
            return self.publish(session, identifier, record)

    def publish(self, session, identifier, record):
        result = record.result
        if not record.logged:
            self.log(session.runtime.session_id, identifier, "run_finished", status=result["status"],
                     questions_asked=result["questions_asked"], error_code=result["error_code"],
                     behavioral_selection=record.behavioral_selection,
                     documents=[{key: source[key] for key in ("document_id", "source", "sha256")}
                                for source in result["sources"]])
            record.logged = True
        if session.runtime.finished:
            self.finish(session)
        return result

    def close(self, identifier):
        with self.exclusive(identifier) as session:
            if not session.runtime.finished:
                session.runtime.close("user_exit")
            self.finish(session)
            self.log(str(identifier), None, "session_closed")
            return self.public(session)

    def logs(self, identifier):
        path = self.directory / "logs" / f"{identifier}.jsonl"
        with self.log_lock:
            if not path.is_file():
                raise ServiceError(404, "session_not_found")
            return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def shutdown(self):
        failures = []
        for identifier in list(self.sessions):
            try:
                self.close(identifier)
            except Exception as error:
                failures.append(error)
                session = self.sessions[identifier]
                if not session.released:
                    session.resources.__exit__(None, None, None)
                    session.released = True
        if failures:
            raise RuntimeError("No se pudieron guardar todas las sesiones al cerrar.") from failures[0]

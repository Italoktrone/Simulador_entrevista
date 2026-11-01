"""Identidad y registro técnico de una sesión, conservados solo en memoria."""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from uuid import uuid4

from harness.interview_config import InterviewSetup
from harness.history_summary import HistorySummaryError
from harness.llm.client import (
    LLMAuthenticationError, LLMConnectionError, LLMContextLimitError, LLMError, LLMInvalidResponseError,
    LLMModelNotFoundError, LLMProviderError, LLMResponse, LLMTimeoutError,
)
from harness.llm.messages import ChatMessage
from harness.profile import ProfileIntegrityError


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def describe_issue(error: BaseException) -> dict[str, str]:
    """Catálogo seguro: no copia mensajes, causas, cuerpos HTTP o credenciales."""
    descriptions = (
        (ProfileIntegrityError, "profile_integrity_error", "No se pudo verificar la integridad del perfil."),
        (KeyboardInterrupt, "interrupted", "La espera fue interrumpida por el usuario."),
        (LLMAuthenticationError, "authentication_error", "El proveedor rechazó la autenticación."),
        (LLMTimeoutError, "timeout", "Se agotó la espera del proveedor."),
        (LLMConnectionError, "connection_error", "No se pudo completar la conexión con el proveedor."),
        (LLMContextLimitError, "context_limit", "El proveedor rechazó la solicitud por falta de espacio de contexto."),
        (HistorySummaryError, "summary_selection_error", "No se obtuvo una selección de fragmentos válida."),
        (LLMModelNotFoundError, "model_not_found", "El proveedor no encontró el modelo solicitado."),
        (LLMInvalidResponseError, "invalid_response", "No se obtuvo una respuesta completa con formato válido."),
        (LLMProviderError, "provider_error", "El proveedor comunicó un error."),
        (LLMError, "llm_error", "No se completó la llamada al modelo."),
    )
    for error_class, code, message in descriptions:
        if isinstance(error, error_class):
            return {"code": code, "error_type": error_class.__name__, "message": message}
    return {"code": "unexpected_error", "error_type": "UnexpectedError", "message": "Ocurrió un error no previsto."}


class SessionState:
    """Registro independiente del proveedor; sus vistas son copias serializables.

    Recibe el escenario validado. No lee archivos ni el entorno, y no guarda
    nada en disco. La configuración no contiene claves o ajustes del cliente.
    """

    def __init__(
        self, setup: InterviewSetup, instructions: str,
        *, provider: str | None = None, model: str | None = None,
    ) -> None:
        for label, value in (("provider", provider), ("model", model)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{label} debe ser texto no vacío o None.")
        if not isinstance(instructions, str) or not instructions.strip():
            raise ValueError("Las instrucciones deben ser texto no vacío.")
        configuration = setup.config_dict()
        self._data = {
            "session_version": "1.0.0",
            "session_id": str(uuid4()),
            "candidate_id": setup.candidate.candidate_id,
            "job_id": configuration["job_id"],
            "configuration": deepcopy(configuration),
            "candidate_source_sha256": setup.candidate.source_sha256,
            "source_integrity": "not_checked",
            "instructions_text_sha256": hashlib.sha256(instructions.encode("utf-8")).hexdigest().upper(),
            "requested_provider": provider,
            "requested_model": model,
            "created_at": _utc_now(),
            "closed_at": None,
            "status": "open",
            "close_reason": None,
            "attempts": [],
            "issues": [],
        }

    @property
    def session_id(self) -> str:
        return self._data["session_id"]

    @property
    def questions_asked(self) -> int:
        return len(self._data["attempts"])

    @property
    def max_questions(self) -> int:
        return self._data["configuration"]["max_questions"]

    @property
    def is_closed(self) -> bool:
        return self._data["status"] == "closed"

    @property
    def has_pending_attempt(self) -> bool:
        return bool(self._data["attempts"] and self._data["attempts"][-1]["status"] == "pending")

    def begin_attempt(self, question: str) -> int:
        if self.is_closed or self.questions_asked >= self.max_questions or self.has_pending_attempt:
            raise ValueError("No se puede iniciar otro intento en el estado actual.")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("La pregunta debe ser texto no vacío.")
        number = self.questions_asked + 1
        self._data["attempts"].append({
            "question_number": number,
            "question": question,
            "requested_at": _utc_now(),
            "finished_at": None,
            "status": "pending",
            "response": None,
            "issues": [],
        })
        return number

    def finish_attempt(
        self, number: int, *, status: str, response: LLMResponse | None,
        issues: list[dict[str, str]],
    ) -> None:
        if not self.has_pending_attempt or self._data["attempts"][-1]["question_number"] != number:
            raise ValueError("El intento indicado no está pendiente.")
        if status not in {"completed", "error", "incomplete", "interrupted"}:
            raise ValueError("Estado final de intento no admitido.")
        if status == "completed" and not isinstance(response, LLMResponse):
            raise ValueError("Un intento completo requiere una respuesta del cliente.")
        self._data["attempts"][-1].update({
            "finished_at": _utc_now(),
            "status": status,
            "response": asdict(response) if isinstance(response, LLMResponse) else None,
            "issues": deepcopy(issues),
        })

    def record_issue(self, error: BaseException) -> None:
        self._data["issues"].append({"recorded_at": _utc_now(), **describe_issue(error)})

    def has_issue(self, code: str) -> bool:
        return any(issue["code"] == code for issue in self._data["issues"]) or any(
            issue["code"] == code
            for attempt in self._data["attempts"] for issue in attempt["issues"]
        )

    def mark_source_integrity(self, valid: bool) -> None:
        if not valid:
            self._data["source_integrity"] = "failed"
        elif self._data["source_integrity"] != "failed":
            self._data["source_integrity"] = "unchanged"

    def close(self, reason: str = "closed") -> None:
        if reason not in {"closed", "user_exit", "question_limit", "end_of_input", "interrupted", "profile_integrity_error"}:
            raise ValueError("Motivo de cierre no admitido.")
        if not self.is_closed:
            self._data.update(status="closed", close_reason=reason, closed_at=_utc_now())

    def history_messages(self) -> list[ChatMessage]:
        messages = []
        for attempt in self._data["attempts"]:
            if attempt["status"] == "completed":
                messages.extend([
                    {"role": "user", "content": attempt["question"]},
                    {"role": "assistant", "content": attempt["response"]["text"]},
                ])
        return messages

    def snapshot(self) -> dict:
        return deepcopy(self._data)

    def enable_context_policy(self, policy: dict) -> None:
        if self.questions_asked or self.is_closed or "context_policy" in self._data:
            raise ValueError("La política debe fijarse una sola vez antes de enviar preguntas.")
        self._data.update(session_version="1.1.0", context_policy=deepcopy(policy), context_events=[])

    def record_context_event(self, event: dict) -> None:
        if "context_events" not in self._data:
            raise ValueError("Esta sesión no tiene una política de contexto activa.")
        self._data["context_events"].append({
            "event_number": len(self._data["context_events"]) + 1,
            "recorded_at": _utc_now(), **deepcopy(event),
        })

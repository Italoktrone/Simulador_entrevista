"""Política y auditoría del resumen en entrevistas, independientes del proveedor."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json

from harness.context_budget import ContextBudget
from harness.history_summary import HistorySummaryError, assemble_summary, build_summary_source


@dataclass(frozen=True, slots=True)
class LiveContextPolicy:
    context_size: int = 8192
    max_output_tokens: int = 512
    safety_margin: int = 256
    trigger_input_tokens: int | None = None
    minimum_completed_pairs: int = 3
    keep_recent_pairs: int = 2

    def __post_init__(self) -> None:
        budget = ContextBudget(self.context_size, self.max_output_tokens, self.safety_margin)
        if self.trigger_input_tokens is None:
            object.__setattr__(self, "trigger_input_tokens", budget.input_limit)
        if type(self.trigger_input_tokens) is not int or not 1 <= self.trigger_input_tokens <= budget.input_limit:
            raise ValueError("El umbral debe estar entre uno y el límite de entrada con reservas.")
        if (type(self.minimum_completed_pairs) is not int or type(self.keep_recent_pairs) is not int or
                not 1 <= self.keep_recent_pairs < self.minimum_completed_pairs <= 19):
            raise ValueError("La política necesita de 1 a 18 pares recientes y más pares completos para activarse, hasta 19.")

    def to_dict(self) -> dict:
        return {"policy_version": "1.0.0", **asdict(self)}

    def reason(self, session: dict, active: bool) -> str:
        completed = [a for a in session["attempts"] if a["status"] == "completed"]
        if len(completed) < self.minimum_completed_pairs:
            return "insufficient_history"
        if active:
            return "already_active"
        if session["attempts"] and any(i["code"] == "context_limit" for i in session["attempts"][-1]["issues"]):
            return "previous_context_limit"
        count = completed[-1]["response"]["input_tokens"]
        if count is not None and count >= self.trigger_input_tokens:
            return "reported_input_tokens"
        return "below_threshold"


def audit_preparation(prepared: dict) -> dict:
    metadata = {k: deepcopy(v) for k, v in prepared.items() if k != "messages"}
    encoded = json.dumps(prepared["messages"], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    metadata["messages_sha256"] = hashlib.sha256(encoded).hexdigest().upper()
    return metadata


def selector_metrics(response) -> dict | None:
    if response is None:
        return None
    return {k: v for k, v in asdict(response).items() if k != "text"}


def validate_live_context_log(data: dict) -> None:
    """Validar auditoría 1.1 después de su esquema, sin consultar archivos o LLM.

    Las citas se reconstruyen desde el prefijo original del historial. Las
    comprobaciones de integridad posteriores no invalidan registros anteriores.
    """
    if data["session_version"] == "1.0.0":
        return
    settings = {k: v for k, v in data["context_policy"].items() if k != "policy_version"}
    policy = LiveContextPolicy(**settings)
    next_question = 1
    active = False
    for number, event in enumerate(data["context_events"], 1):
        if event["event_number"] != number or event["before_question_number"] != next_question:
            raise HistorySummaryError("La auditoría de contexto no conserva el orden de preparación de preguntas.")
        prefix = deepcopy(data)
        prefix["attempts"] = data["attempts"][:next_question - 1]
        prefix["source_integrity"] = "unchanged"
        reason = policy.reason(prefix, active)
        if event["trigger_reason"] != reason:
            raise HistorySummaryError("La activación registrada no coincide con la política y el historial previo.")
        requested = reason not in {"insufficient_history", "below_threshold"}
        active |= requested
        status = event["selector_status"]
        if requested == (status == "not_requested"):
            raise HistorySummaryError("La selección registrada no coincide con su activación.")
        if status in {"failed", "interrupted"} and not event["issues"]:
            raise HistorySummaryError("La selección fallida necesita una incidencia técnica.")
        if status == "not_requested" and (event["summary_selections"] is not None or event["selector_metrics"] is not None or event["issues"]):
            raise HistorySummaryError("Una selección no solicitada no puede contener resultados o errores del selector.")
        if status == "failed" and event["summary_selections"] is not None:
            raise HistorySummaryError("Una selección fallida no puede conservar índices como aceptados.")
        if status == "completed" and event["issues"]:
            raise HistorySummaryError("Una selección completa no puede contener incidencias.")
        source = build_summary_source(prefix, keep_recent_pairs=policy.keep_recent_pairs)
        summary = None
        if event["summary_selections"] is not None:
            summary = assemble_summary(source, event["summary_selections"])
        if status == "completed" and (summary is None or event["selector_metrics"] is None):
            raise HistorySummaryError("La selección completa necesita índices y métricas del cliente.")
        prepared = event["preparation"]
        if event["candidate_sent"]:
            if prepared is None or next_question > len(data["attempts"]):
                raise HistorySummaryError("Falta la preparación de una pregunta enviada.")
            next_question += 1
        elif prepared is not None or status not in {"interrupted", "aborted"}:
            raise HistorySummaryError("Una preparación abortada no puede figurar como enviada.")
        if prepared is None:
            continue
        if (prepared["source_session_id"] != data["session_id"] or
                prepared["source_history_sha256"] != source["source_history_sha256"]):
            raise HistorySummaryError("La preparación no coincide con el prefijo del historial original.")
        full, proposed, selected, saved = (prepared[k] for k in ("full_message_bytes", "proposed_message_bytes", "selected_message_bytes", "saved_message_bytes"))
        if prepared["mode"] == "extractive_summary":
            if (status != "completed" or summary["statistics"]["omitted_segments"] == 0 or
                    not proposed < full or selected != proposed or saved != full - proposed or
                    prepared["reason"] != "smaller_message_json"):
                raise HistorySummaryError("La auditoría no demuestra el ahorro declarado de mensajes.")
        elif selected != full or saved != 0 or prepared["reason"] == "smaller_message_json":
            raise HistorySummaryError("La preparación completa contiene medidas incompatibles.")
        if status == "failed" and prepared["reason"] != "selector_failed":
            raise HistorySummaryError("El fallo del selector debe conservar la decisión de respaldo.")
        if status in {"not_requested", "failed"} and (prepared["mode"] != "full_history" or proposed != full):
            raise HistorySummaryError("El contexto sin selección aceptada debe conservar los mensajes completos.")
        if status == "not_requested" and prepared["reason"] != "no_omissions":
            raise HistorySummaryError("Una preparación sin selección debe conservar todos los fragmentos.")
        if status == "completed":
            reduced = summary["statistics"]["omitted_segments"] > 0 and proposed < full
            expected_reason = "smaller_message_json" if reduced else ("no_omissions" if not summary["statistics"]["omitted_segments"] else "no_byte_savings")
            if prepared["reason"] != expected_reason or (prepared["mode"] == "extractive_summary") != reduced:
                raise HistorySummaryError("La decisión no coincide con la selección y las medidas registradas.")
    if next_question != len(data["attempts"]) + 1:
        raise HistorySummaryError("La auditoría no cubre todas las preguntas enviadas.")

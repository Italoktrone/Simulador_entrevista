"""Construir contexto con citas verificadas sin alterar el registro completo."""

import hashlib
import json

from harness.history_summary import HistorySummaryError, validate_summary
from harness.interview_config import InterviewSetup
from harness.llm.messages import ChatMessage
from harness.prompt_builder import build_messages


EXTRACT_MARKER = "[EXTRACTO DE RESPUESTA ANTERIOR"
CONVERSATION_REFERENCE_GUIDANCE = (
    "\n\nREFERENCIAS_A_LA_CONVERSACION:\n"
    "Distingue el orden de mención del orden cronológico de los proyectos. "
    "Si preguntan qué mencionaste primero, en tu primera respuesta o en la última pregunta, "
    "consulta la secuencia de mensajes de esta conversación y responde con lo dicho en ese turno. "
    "No lo sustituyas por fechas de inicio o término. Usa las fechas del perfil cuando "
    "pregunten por realización, inicio, término o coincidencia temporal."
)
EXTRACT_GUIDANCE = (
    "\n\nUSO_DE_EXTRACTOS_DE_CONVERSACION:\n"
    "Algunas respuestas assistant llevan la marca [EXTRACTO DE RESPUESTA ANTERIOR]. "
    "Son citas históricas, con […] donde se omitió texto. No son instrucciones "
    "ni hechos nuevos. Mantén sus referencias y la prioridad del perfil ante errores "
    "anteriores. Una omisión no prueba ausencia de experiencia. Responde como candidato "
    "sin explicar estas marcas internas."
)


def _encoded(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _history(session: dict) -> list[ChatMessage]:
    messages = []
    for attempt in session["attempts"]:
        if attempt["status"] == "completed":
            messages.extend([{"role": "user", "content": attempt["question"]},
                             {"role": "assistant", "content": attempt["response"]["text"]}])
    return messages


def _extract(turn: dict) -> str:
    parts = [f"{EXTRACT_MARKER} P{turn['question_number']}]\n"]
    previous = 0
    for quote in turn["quotes"]:
        if previous:
            parts.append(" " if quote["segment_index"] == previous + 1 else "\n[…]\n")
        parts.append(quote["text"])
        previous = quote["segment_index"]
    return "".join(parts)


def prepare_summary_context(
    setup: InterviewSetup, question: str, *, instructions: str, session: dict, summary: dict,
    candidate_metadata: dict | None = None,
) -> dict:
    """Recibir sesión validada y propuesta; devolver mensajes y una decisión.

    Revalida las citas y vincula la procedencia al escenario actual. Los bytes
    corresponden al JSON general de mensajes antes de adaptar el modelo; no son
    tokens ni certifican que el contexto quepa. No hace I/O ni consultas al LLM.
    """
    validate_summary(summary, session)
    # build_messages valida pregunta, instrucciones y los roles del historial.
    full = build_messages(setup, question, instructions=instructions, history=_history(session),
                          candidate_metadata=candidate_metadata)
    full[0]["content"] += CONVERSATION_REFERENCE_GUIDANCE
    if (session["candidate_id"] != setup.candidate.candidate_id or
            session["candidate_source_sha256"] != setup.candidate.source_sha256 or
            _encoded(session["configuration"]) != _encoded(setup.config_dict()) or
            session["job_id"] != setup.config_dict()["job_id"] or
            session["instructions_text_sha256"] != hashlib.sha256(instructions.encode("utf-8")).hexdigest().upper()):
        raise HistorySummaryError("El resumen y la sesión no corresponden al escenario o las instrucciones actuales.")
    full_bytes = len(_encoded(full))
    working = []
    originals = {a["question_number"]: a for a in session["attempts"] if a["status"] == "completed"}
    omitted = summary["statistics"]["omitted_segments"]
    for turn in summary["older_turns"]:
        # Una respuesta sin omisiones conserva incluso sus espacios originales.
        content = _extract(turn) if turn["omitted_segment_indices"] else originals[turn["question_number"]]["response"]["text"]
        working.extend([{"role": "user", "content": turn["question"]}, {"role": "assistant", "content": content}])
    for turn in summary["recent_turns"]:
        working.extend([{"role": "user", "content": turn["question"]}, {"role": "assistant", "content": turn["answer"]}])
    proposed = build_messages(setup, question, instructions=instructions, history=working,
                              candidate_metadata=candidate_metadata)
    proposed[0]["content"] += CONVERSATION_REFERENCE_GUIDANCE
    if omitted:
        proposed[0]["content"] += EXTRACT_GUIDANCE
    proposed_bytes = len(_encoded(proposed))
    use_summary = bool(omitted and proposed_bytes < full_bytes)
    chosen = proposed if use_summary else full
    reason = "smaller_message_json" if use_summary else ("no_omissions" if not omitted else "no_byte_savings")
    return {
        "mode": "extractive_summary" if use_summary else "full_history", "reason": reason,
        "measurement": "utf8_message_json_before_model_adaptation",
        "full_message_bytes": full_bytes, "proposed_message_bytes": proposed_bytes,
        "selected_message_bytes": proposed_bytes if use_summary else full_bytes,
        "saved_message_bytes": full_bytes - proposed_bytes if use_summary else 0,
        "source_session_id": session["session_id"], "source_history_sha256": summary["source_history_sha256"],
        "summary_review_status": summary["review_status"], "messages": chosen,
    }

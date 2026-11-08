"""Contexto acotado y validación del registro de clasificación previo al candidato."""

from copy import deepcopy
from pathlib import Path

from harness.classification_contract import validate_classification
from harness.json_loader import load_json
from harness.response_policy import decide_response
from harness.schema_validator import validate_data


ROOT = Path(__file__).resolve().parents[1]
INTERVENTION_SCHEMA_PATH = ROOT / "schemas/intervention.schema.json"
CONTEXT_PAIRS = 2
CONTEXT_CHARACTERS = 1200


def classification_configuration(info: dict | None = None) -> dict:
    info = {} if info is None else deepcopy(info)
    allowed = {"requested_provider", "requested_model", "max_output_tokens"}
    if not isinstance(info, dict) or set(info) - allowed:
        raise ValueError("Los datos del clasificador solo admiten proveedor, modelo y presupuesto.")
    result = {"policy_version": "1.0.0", "context_pairs": CONTEXT_PAIRS,
            "characters_per_message": CONTEXT_CHARACTERS,
            "requested_provider": info.get("requested_provider"),
            "requested_model": info.get("requested_model"), "max_output_tokens": info.get("max_output_tokens")}
    schema = load_json(INTERVENTION_SCHEMA_PATH)
    validate_data(result, {"$defs": schema["$defs"], "$ref": "#/$defs/configuration"})
    return result


def select_classification_context(attempts: list[dict]) -> list[dict]:
    """Prefijos literales de dos pares completos; no resume ni consulta un LLM."""
    completed = [attempt for attempt in attempts if attempt["status"] == "completed"]
    def fragment(text):
        start = len(text) - len(text.lstrip())
        return text[start:start + CONTEXT_CHARACTERS]
    return [{"turn_number": attempt["question_number"], "messages": [
        {"role": "user", "content": fragment(attempt["question"])},
        {"role": "assistant", "content": fragment(attempt["response"]["text"])},
    ]} for attempt in completed[-CONTEXT_PAIRS:]]


def validate_interventions(data: dict) -> None:
    """Revalidar etiquetas, política, fuentes y cobertura sin llamar al proveedor."""
    if data["session_version"] not in {"1.2.0", "1.3.0"}:
        return
    schema = load_json(INTERVENTION_SCHEMA_PATH)
    validate_data(data["classification_policy"], {"$defs": schema["$defs"], "$ref": "#/$defs/configuration"})
    next_question = 1
    for number, event in enumerate(data["interventions"], 1):
        validate_data(event, schema)
        if (event["intervention_number"] != number or event["intervention_id"] != f"{data['session_id']}:i{number}"
                or event["before_question_number"] != next_question or next_question > data["configuration"]["max_questions"]):
            raise ValueError("Las intervenciones no conservan orden, identidad o contador.")
        context = select_classification_context(data["attempts"][:next_question - 1])
        ids = tuple(turn["turn_number"] for turn in context)
        if event["available_context_turn_ids"] != list(ids):
            raise ValueError("El contexto no corresponde a los turnos completos previos de esta sesión.")
        report = event["classification"]
        policy = event["policy"]
        if report is not None:
            result = validate_classification(report["result"], expected_intervention_id=event["intervention_id"],
                                             expected_text=event["text"], allowed_context_turn_ids=ids)
            expected_policy = decide_response(result, expected_intervention_id=event["intervention_id"],
                                              expected_text=event["text"], allowed_context_turn_ids=ids).to_dict()
            if policy != expected_policy:
                raise ValueError("La política registrada no coincide con las etiquetas validadas.")
            if report["status"] != ("respaldo" if result["technical_error"] is not None else "clasificada"):
                raise ValueError("El estado del híbrido no coincide con su resultado.")
            local, llm = report["trace"]["local"], report["trace"]["llm"]
            if report["route"] == "reglas":
                if (llm is not None or local["status"] != "clasificada" or result["method"] != "reglas"
                        or local["reason_code"] != "regla_aplicada"):
                    raise ValueError("Procedencia local incompatible.")
            else:
                if llm is None or local["status"] != "abstencion" or result["method"] not in {"llm", "respaldo"}:
                    raise ValueError("Procedencia semántica incompatible.")
                attempts = llm["attempts"]
                if "aggregation_applied" in llm and llm["aggregation_applied"] != (
                        result["technical_error"] is None and result["evaluability"] == "evaluable"):
                    raise ValueError("La procedencia de los derivados no coincide con el resultado.")
                if local["reason_code"] == "regla_aplicada" or llm["status"] != report["status"]:
                    raise ValueError("La auditoría de enrutamiento es incompatible.")
                if [attempt["number"] for attempt in attempts] != list(range(1, len(attempts) + 1)):
                    raise ValueError("Los intentos de clasificación no están numerados consecutivamente.")
                if len(attempts) == 2 and attempts[0]["status"] not in {"json_invalido", "contrato_invalido"}:
                    raise ValueError("No se permite reparar un fallo del proveedor.")
                if (attempts[-1]["status"] == "validada") != (result["technical_error"] is None):
                    raise ValueError("La auditoría LLM no coincide con el resultado técnico.")
                for attempt in attempts:
                    state, code = attempt["status"], attempt["error_code"]
                    if attempt.get("validation_error") is not None and state != "contrato_invalido":
                        raise ValueError("Solo un fallo de contrato admite detalle de validación.")
                    if ((state == "validada" and code is not None)
                            or (state in {"json_invalido", "contrato_invalido"} and code != state)
                            or (state == "error_proveedor" and code in {None, "json_invalido", "contrato_invalido"})):
                        raise ValueError("Los códigos de intento no coinciden con sus estados.")
                expected_error = None if attempts[-1]["status"] == "validada" else attempts[-1]["status"]
                if result["technical_error"] != expected_error:
                    raise ValueError("El código terminal no coincide con el último intento.")
        elif policy is not None or event["candidate_question_number"] is not None:
            raise ValueError("No se permite política o envío sin clasificación.")
        sent = event["candidate_question_number"]
        if sent is not None:
            if sent != next_question or sent > len(data["attempts"]) or policy["action"] != "responder":
                raise ValueError("Envío no autorizado o contador incompatible.")
            attempt = data["attempts"][sent - 1]
            if attempt["question"] != event["text"] or attempt["status"] != event["status"] or attempt["issues"] != event["issues"]:
                raise ValueError("La intervención no corresponde al intento del candidato.")
            next_question += 1
        elif event["status"] == "handled":
            if policy is None or policy["action"] == "responder" or event["issues"]:
                raise ValueError("Una intervención atendida sin envío necesita una política compatible.")
        elif event["status"] not in {"error", "interrupted"} or not event["issues"]:
            raise ValueError("Un envío ausente debe estar atendido o conservar una incidencia.")
    if next_question != len(data["attempts"]) + 1:
        raise ValueError("La bitácora no cubre todas las preguntas enviadas.")

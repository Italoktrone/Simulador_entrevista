"""Política mínima de respuesta, separada de etiquetas y generación del candidato."""

from dataclasses import dataclass, field
import json

from harness.classification_contract import SCHEMA_PATH, validate_classification
from harness.json_loader import load_json
from harness.schema_validator import validate_data


POLICY_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ResponsePolicyDecision:
    action: str
    code: str
    text: str | None
    _metadata_json: str | None = field(default=None, repr=False)

    @property
    def candidate_metadata(self) -> dict | None:
        return None if self._metadata_json is None else json.loads(self._metadata_json)

    def to_dict(self) -> dict:
        return {"policy_version": POLICY_VERSION, "action": self.action, "code": self.code,
                "text": self.text, "candidate_metadata": self.candidate_metadata}


def validate_candidate_metadata(metadata: object) -> dict:
    """Solo códigos autorizados; jamás texto del modelo como instrucción system."""
    source = load_json(SCHEMA_PATH)
    props = source["$defs"]["classification"]["properties"]
    schema = {
        "type": "object", "additionalProperties": False,
        "required": ["policy_version", "action", "approaches", "forms", "attributes", "certainty"],
        "$defs": source["$defs"],
        "properties": {
            "policy_version": {"const": POLICY_VERSION}, "action": {"const": "responder"},
            "approaches": {"type": "array", "minItems": 1, "uniqueItems": True,
                           "items": source["$defs"]["known_approach"]},
            "forms": {"type": "array", "minItems": 1, "uniqueItems": True,
                      "items": {"enum": [value for value in source["$defs"]["form"]["enum"] if value != "indeterminada"]}},
            "attributes": props["attributes"], "certainty": {"const": "clara"},
        },
    }
    validate_data(metadata, schema)
    return json.loads(json.dumps(metadata, ensure_ascii=False, allow_nan=False))


def decide_response(classification: dict, *, expected_intervention_id: str,
                    expected_text: str, allowed_context_turn_ids: tuple[int, ...] = ()) -> ResponsePolicyDecision:
    """Revalidar datos de origen antes de autorizar cualquier efecto."""
    result = validate_classification(
        classification, expected_intervention_id=expected_intervention_id,
        expected_text=expected_text, allowed_context_turn_ids=allowed_context_turn_ids,
    )
    if result["technical_error"] is not None:
        return ResponsePolicyDecision("error_tecnico", "fallo_clasificacion",
                                      "No se pudo clasificar la intervención por un fallo técnico. No se envió al candidato.")
    if result["evaluability"] == "no_evaluable":
        return ResponsePolicyDecision("no_evaluable", "entrada_no_evaluable",
                                      "Intervención registrada. Formula una pregunta de entrevista para continuar.")
    labels = result["classification"]
    if labels["certainty"] != "clara":
        return ResponsePolicyDecision("aclarar", "contexto_o_intencion_insuficiente",
                                      "Reformula la pregunta incluyendo la situación o el dato al que te refieres.")
    metadata = validate_candidate_metadata({
        "policy_version": POLICY_VERSION, "action": "responder", "approaches": labels["approaches"],
        "forms": labels["forms"], "attributes": labels["attributes"], "certainty": labels["certainty"],
    })
    return ResponsePolicyDecision("responder", "clasificacion_clara", None,
                                  json.dumps(metadata, ensure_ascii=False, allow_nan=False))

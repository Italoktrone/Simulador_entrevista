"""Validación del contrato descriptivo; no clasifica ni consulta un proveedor."""

from copy import deepcopy
import json
from pathlib import Path

from harness.json_loader import load_json
from harness.schema_validator import DataValidationError, validate_data


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/question_classification.schema.json"


class ClassificationContractError(DataValidationError):
    """Estructura o relaciones incompatibles, sin copiar contenido rechazado."""


def _require(condition: bool, path: str, rule: str, detail: str) -> None:
    if not condition:
        raise ClassificationContractError(path, rule, detail)


def _validate_labels(labels: dict, path: str, *, unit: bool = False) -> None:
    for plural, main, reason, unknown in (
        ("approaches", "main_approach", "main_approach_reason", "indeterminado"),
        ("forms", "main_form", "main_form_reason", "indeterminada"),
    ):
        present = set(labels[plural])
        primary = labels[main]
        _require(unknown not in present or len(present) == 1, f"{path}/{plural}",
                 "unknown_exclusive", "La etiqueta indeterminada no puede acompañar etiquetas definidas.")
        _require(primary in present if primary is not None else len(present) > 1,
                 f"{path}/{main}", "primary_membership", "El principal debe pertenecer al conjunto; null requiere varios valores definidos.")
        needs_reason = len(present) > 1 and primary is not None
        _require((labels[reason] is not None) == needs_reason, f"{path}/{reason}",
                 "dominance_reason", "La selección de un principal entre varios valores requiere una razón exclusiva para esa prioridad.")
    primary = labels["main_approach"]
    expected = set(labels["approaches"]) - {primary} if primary is not None else set()
    expected.discard("indeterminado")
    _require(set(labels["secondary_approaches"]) == expected, f"{path}/secondary_approaches",
             "secondary_consistency", "Los secundarios deben ser todos los enfoques presentes salvo el principal; sin principal no hay secundarios jerarquizados.")
    if unit:
        _require(len(labels["forms"]) == 1, f"{path}/forms", "unit_form",
                 "Cada unidad necesita una sola forma; separar peticiones si tienen formas diferentes.")
        if labels["certainty"] == "clara":
            _require(labels["approaches"] != ["indeterminado"] and labels["forms"] != ["indeterminada"],
                     f"{path}/certainty", "certainty_consistency", "Una unidad clara no puede tener dimensiones indeterminadas.")
        if labels["certainty"] == "indeterminada":
            _require(labels["approaches"] == ["indeterminado"] or labels["forms"] == ["indeterminada"],
                     f"{path}/certainty", "certainty_consistency", "La certeza indeterminada requiere al menos una dimensión indeterminada.")


def _union(units: list[dict], field: str, unknown: str | None = None) -> set[str]:
    values = {value for unit in units for value in unit["classification"][field]}
    if unknown is not None and len(values) > 1:
        values.discard(unknown)
    return values


def validate_classification(
    data: object, *, expected_intervention_id: str, expected_text: str,
    allowed_context_turn_ids: tuple[int, ...] = (),
) -> dict:
    """Devolver una copia validada contra datos de origen confiables.

    El llamador aporta identidad, texto original y turnos disponibles de su
    propia sesión. validation_status nunca evita validar de nuevo. No interpreta
    justificaciones como instrucciones ni comprueba su verdad semántica.
    """
    result = _validate_document(
        data, load_json(SCHEMA_PATH), expected_intervention_id=expected_intervention_id,
        expected_text=expected_text, allowed_context_turn_ids=allowed_context_turn_ids,
    )
    result["validation_status"] = "validada"
    return result


def validate_classification_expectation(
    data: object, *, expected_intervention_id: str, expected_text: str,
    allowed_context_turn_ids: tuple[int, ...] = (),
) -> dict:
    """Validar etiquetas de referencia sin atribuirles ejecución de reglas o LLM.

    Reutiliza el contrato y sus relaciones. Excluye método, reglas, error técnico
    y sello de validación: una expectativa humana no es un resultado generado.
    """
    return _validate_document(
        data, classification_expectation_schema(), expected_intervention_id=expected_intervention_id,
        expected_text=expected_text, allowed_context_turn_ids=allowed_context_turn_ids,
        check_provenance=False,
    )


def classification_expectation_schema() -> dict:
    """Esquema de etiquetas sin procedencia de ejecución, también apto para el LLM.

    Devuelve una copia nueva. Las relaciones entre campos siguen requiriendo
    validate_classification_expectation; el esquema solo comprueba estructura.
    """
    schema = load_json(SCHEMA_PATH)
    execution_fields = {"method", "rule_ids", "technical_error", "validation_status"}
    schema["required"] = [key for key in schema["required"] if key not in execution_fields]
    for key in execution_fields:
        schema["properties"].pop(key)
    schema["properties"]["evaluability"]["enum"] = ["evaluable", "no_evaluable"]
    # Solo conservar alternativas de evaluabilidad, sin estados de ejecución.
    branches = []
    for branch in schema["allOf"]:
        condition = branch["if"]["properties"].get("evaluability", {})
        if condition.get("const") in {"evaluable", "no_evaluable"}:
            props = branch["then"]["properties"]
            for key in execution_fields:
                props.pop(key, None)
            branches.append(branch)
    schema["allOf"] = branches
    unit = schema["$defs"]["unit"]
    unit["required"] = [key for key in unit["required"] if key not in execution_fields]
    for key in ("method", "rule_ids"):
        unit["properties"].pop(key)
    unit.pop("allOf")
    return schema


def _validate_document(
    data: object, schema: dict, *, expected_intervention_id: str, expected_text: str,
    allowed_context_turn_ids: tuple[int, ...], check_provenance: bool = True,
) -> dict:
    if not isinstance(expected_intervention_id, str) or not expected_intervention_id:
        raise ValueError("Se necesita un identificador de intervención confiable.")
    if not isinstance(expected_text, str):
        raise ValueError("El texto original confiable debe ser una cadena.")
    if (not isinstance(allowed_context_turn_ids, tuple)
            or any(type(number) is not int or number < 1 for number in allowed_context_turn_ids)
            or len(set(allowed_context_turn_ids)) != len(allowed_context_turn_ids)):
        raise ValueError("Los turnos autorizados deben ser una tupla de enteros positivos únicos.")
    try:
        json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ClassificationContractError("/", "json_value", "Se requieren datos JSON UTF-8 válidos.") from None
    # Validar también evita que valores Python ajenos a JSON pasen como objetos.
    try:
        validate_data(data, schema, detailed_errors=True)
    except DataValidationError as error:
        raise ClassificationContractError(error.path, error.rule, error.detail) from None
    result = deepcopy(data)
    _require(result["intervention_id"] == expected_intervention_id, "/intervention_id",
             "source_identity", "El identificador no coincide con la intervención de origen.")
    _require(result["original_text"] == expected_text, "/original_text", "source_text",
             "El texto debe coincidir exactamente con la intervención de origen.")
    context_ids = result["context_turn_ids"]
    # JSON Schema admite 1.0 como entero; los identificadores y offsets se exigen int en Python.
    _require(all(type(number) is int for number in context_ids), "/context_turn_ids",
             "integer_identity", "Los identificadores de turno deben ser enteros, sin decimales.")
    _require(set(context_ids) <= set(allowed_context_turn_ids), "/context_turn_ids",
             "context_scope", "Solo se permite contexto proporcionado por el llamador para esta sesión.")
    status = result["evaluability"]
    if status == "evaluable":
        _validate_evaluable(result)
        if check_provenance:
            _validate_provenance(result)
    elif status == "no_evaluable":
        empty = not result["original_text"].strip()
        _require((result["non_evaluable_reason"] == "vacia") == empty, "/non_evaluable_reason",
                 "empty_reason", "El motivo vacía debe corresponder exactamente a texto vacío o de espacios.")
    else:
        labels = result["classification"]
        _validate_labels(labels, "/classification")
        _require(labels["approaches"] == ["indeterminado"] and labels["forms"] == ["indeterminada"]
                 and labels["certainty"] == "indeterminada" and not labels["attributes"],
                 "/classification", "technical_fallback", "Un respaldo técnico no puede inventar etiquetas.")
    return result


def _validate_evaluable(result: dict) -> None:
    units = result["units"]
    previous_end = 0
    for index, unit in enumerate(units):
        path = f"/units/{index}"
        _require(unit["unit_id"] == f"u{index + 1}", path + "/unit_id", "unit_sequence",
                 "Las unidades deben numerarse consecutivamente desde u1.")
        start, end = unit["source_start"], unit["source_end"]
        _require(type(start) is int and type(end) is int, path, "integer_offset",
                 "Las posiciones deben ser enteros, sin decimales.")
        _require(previous_end <= start < end <= len(result["original_text"]), path,
                 "source_span", "Los fragmentos deben estar ordenados, dentro del original y sin solapamiento.")
        _require(unit["text"] == result["original_text"][start:end], path + "/text",
                 "unit_source_text", "Cada unidad debe copiar exactamente su fragmento original.")
        previous_end = end
        dependency = unit["depends_on"]
        _require(dependency is None or dependency in {item["unit_id"] for item in units[:index]},
                 path + "/depends_on", "unit_dependency", "Una dependencia debe apuntar a una unidad anterior de esta intervención.")
        followup = unit["followup_of"]
        _require(followup is None or type(followup) is int and followup in result["context_turn_ids"],
                 path + "/followup_of", "followup_scope", "La repregunta debe referir un turno autorizado y declarado como utilizado.")
        context_status = unit["context_status"]
        if context_status == "no_necesario":
            _require(followup is None, path + "/followup_of", "followup_context",
                     "Una repregunta vinculada necesita contexto.")
        if context_status == "suficiente":
            _require(bool(result["context_turn_ids"]), path + "/context_status", "context_evidence",
                     "El contexto suficiente debe identificar al menos un turno utilizado.")
        if context_status == "insuficiente":
            _require(unit["classification"]["certainty"] != "clara", path + "/classification/certainty",
                     "missing_context", "No se puede declarar clara una unidad con contexto insuficiente.")
        _validate_labels(unit["classification"], path + "/classification", unit=True)
    global_labels = result["classification"]
    _validate_labels(global_labels, "/classification")
    if len(units) == 1:
        _require(all(global_labels[field] == units[0]["classification"][field]
                     for field in ("main_approach", "main_form")), "/classification",
                 "single_unit_primary", "Con una sola unidad, sus principales y los globales deben coincidir.")
    for field, unknown in (("approaches", "indeterminado"), ("forms", "indeterminada"), ("attributes", None)):
        _require(set(global_labels[field]) == _union(units, field, unknown), f"/classification/{field}",
                 "global_union", "El conjunto global debe coincidir con la unión de las unidades; la incertidumbre permanece en cada unidad.")
    certainties = {unit["classification"]["certainty"] for unit in units}
    expected_certainty = ("clara" if certainties == {"clara"} else
                          "indeterminada" if certainties == {"indeterminada"} else "ambigua")
    _require(global_labels["certainty"] == expected_certainty, "/classification/certainty",
             "global_certainty", "La certeza global no coincide con las certezas de las unidades.")


def _validate_provenance(result: dict) -> None:
    units = result["units"]
    methods = {unit["method"] for unit in units}
    expected_method = next(iter(methods)) if len(methods) == 1 else "hibrido"
    _require(result["method"] == expected_method, "/method", "global_method",
             "El método global debe reflejar los métodos realmente declarados en las unidades.")
    _require(set(result["rule_ids"]) == {rule for unit in units for rule in unit["rule_ids"]},
             "/rule_ids", "global_rules", "Las reglas globales deben ser la unión de las aplicadas por unidad.")

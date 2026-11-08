"""Contratos separados: evidencia del LLM y registro calculado por Python."""

from copy import deepcopy
from jsonschema import Draft202012Validator, ValidationError

from harness.scoring import CRITERIA, LEVELS, score_criteria, validate_rubric
from harness.schema_validator import DataValidationError, validate_data

EVALUATION_VERSION = "1.2.0"
RECORD_VERSION = "1.3.0"
DEMONSTRATION_CASES = ("E03", "E05", "E07", "E08", "E12", "E15")


class EvaluationContractError(ValueError):
    """Código estable y diagnóstico controlado, sin copiar valores rechazados."""

    def __init__(self, code, path, rule, detail):
        self.code, self.path, self.rule, self.detail = code, path, rule, detail
        super().__init__(code)

    def audit(self):
        return {"path": self.path, "rule": self.rule, "message": self.detail}


def _validate_structure(value, schema):
    try:
        validate_data(value, schema, detailed_errors=True)
    except DataValidationError as error:
        # Solo nombres definidos por nosotros e índices; no claves del modelo.
        allowed = set()
        def collect(node):
            if isinstance(node, dict):
                allowed.update(node.get("properties", {}))
                for child in node.values():
                    collect(child)
            elif isinstance(node, list):
                for child in node:
                    collect(child)
        collect(schema)
        path = "/" if error.path == "raíz" else "/".join(
            part if not part or part in allowed or part.isascii() and part.isdigit() else "[REDACTED]"
            for part in error.path.split("/"))
        detail = error.detail
        schema_error = error.__cause__
        # validator_value procede de nuestro esquema, no del valor rechazado.
        if (isinstance(schema_error, ValidationError)
                and error.rule in {"maxLength", "minLength", "maxItems", "minItems", "maximum", "minimum"}
                and type(schema_error.validator_value) is int):
            detail += f" Límite: {schema_error.validator_value}."
        raise EvaluationContractError("contrato_invalido", path, error.rule, detail) from None


def _object(properties):
    return {"type": "object", "additionalProperties": False,
            "required": list(properties), "properties": properties}


def _text(maximum=500):
    return {"type": "string", "minLength": 1, "maxLength": maximum, "pattern": "\\S"}


def analysis_schema(version="1.0.0"):
    evidence = _object({"source": {"enum": ["question", "context_question", "context_answer"]},
                        "turn_number": {"type": ["integer", "null"], "minimum": 1}, "quote": _text(500)})
    criterion = _object({"level": {"type": ["integer", "null"], "minimum": 1, "maximum": 4},
                         "evidence": {"type": "array", "maxItems": 3, "items": evidence},
                         "reason": _text(350), "suggestion": {"anyOf": [{"type": "null"}, _text(250)]},
                         "reformulation": {"anyOf": [{"type": "null"}, _text(500)]}})
    discrepancy = _object({"field": {"enum": ["approaches", "forms", "attributes", "evaluability"]},
                           "alternative": _text(160), "reason": _text(250), "quote": _text(500)})
    return _object({"contract_version": {"const": version},
                    "applicability": {"enum": ["evaluable", "no_evaluable"]}, "reason": _text(350),
                    "criteria": _object({key: deepcopy(criterion) for key in CRITERIA}),
                    "discrepancies": {"type": "array", "maxItems": 4, "items": discrepancy}})


def llm_evaluation_schema(*, allowed_context_turn_numbers=None):
    """Protocolo 1.2: nivel observado con cita, fuente y turno compatibles."""
    legacy = analysis_schema()
    question_evidence = _object({"source": {"const": "question"}, "turn_number": {"type": "null"}, "quote": _text(160)})
    context_evidence = _object({"source": {"enum": ["context_question", "context_answer"]},
                                "turn_number": {"type": "integer", "minimum": 1}, "quote": _text(160)})
    if allowed_context_turn_numbers is not None:
        numbers = list(allowed_context_turn_numbers)
        if any(type(n) is not int or not 1 <= n <= 20 for n in numbers):
            raise ValueError("Turnos de contexto inválidos.")
        numbers = sorted(set(numbers))
        context_evidence["properties"]["turn_number"] = {"enum": numbers}
    evidence = {"oneOf": [question_evidence, context_evidence]} if allowed_context_turn_numbers is None or numbers else question_evidence
    observed = _object({"level": {"type": "integer", "minimum": 1, "maximum": 4},
                         "evidence_ids": {"type": "array", "minItems": 1, "maxItems": 2, "uniqueItems": True,
                                          "items": {"type": "integer", "minimum": 0, "maximum": 5}},
                         "reason": _text(110)})
    missing = _object({"level": {"type": "null"}, "evidence_ids": {"type": "array", "maxItems": 0}, "reason": _text(110)})
    criterion = {"oneOf": [observed, missing]}
    schema = _object({"contract_version": {"const": EVALUATION_VERSION},
                    "applicability": {"enum": ["evaluable", "no_evaluable"]}, "reason": _text(120),
                    "evidence": {"type": "array", "maxItems": 6, "items": evidence},
                    "criteria": _object({k: {"$ref": "#/$defs/criterion"} for k in CRITERIA}),
                    "feedback": _object({"criterion": {"enum": [None, *CRITERIA]},
                                         "suggestion": {"anyOf": [{"type": "null"}, _text(160)]},
                                         "reformulation": {"anyOf": [{"type": "null"}, _text(220)]}}),
                    "discrepancies": deepcopy(legacy["properties"]["discrepancies"])})
    # Una definición compartida evita repetir cuatro veces las mismas reglas
    # tanto en el prompt como en el formato nativo, sin relajar el contrato.
    schema["$defs"] = {"criterion": criterion}
    return schema


def evaluation_generation_schema(*, allowed_context_turn_numbers=None, classification_available=None):
    """Formato nativo: priorizar límites de longitud ante el conflicto pattern.

    Algunos conversores GBNF ignoran minLength/maxLength al encontrar pattern.
    La comprobación de texto no blanco sigue intacta en el contrato Python.
    """
    schema = llm_evaluation_schema(allowed_context_turn_numbers=allowed_context_turn_numbers)
    if classification_available is not None and type(classification_available) is not bool:
        raise ValueError("classification_available debe ser booleano o null.")
    if classification_available is False:
        schema["properties"]["discrepancies"]["maxItems"] = 0
    def visit(node):
        if isinstance(node, dict):
            if node.get("pattern") == r"\S" and "maxLength" in node:
                del node["pattern"]
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(schema)
    return schema


def complete_evaluation(draft, request):
    """Expandir referencias exactas de citas. No completar niveles ni evidencias."""
    schema = llm_evaluation_schema()
    # Elegir por discriminantes antes de diagnosticar: best_match puede señalar
    # la rama null ante un reason demasiado largo en un criterio puntuado.
    # No se altera el dato ni se admite ninguna combinación adicional.
    if isinstance(draft, dict):
        criteria = draft.get("criteria")
        if isinstance(criteria, dict):
            for key in CRITERIA:
                item = criteria.get(key)
                if isinstance(item, dict):
                    branches = schema["$defs"]["criterion"]["oneOf"]
                    schema["properties"]["criteria"]["properties"][key] = branches[1 if item.get("level") is None else 0]
        pool = draft.get("evidence")
        if isinstance(pool, list) and pool:
            alternatives = schema["properties"]["evidence"]["items"]["oneOf"]
            schema["properties"]["evidence"]["prefixItems"] = [
                alternatives[0 if item["source"] == "question" else 1]
                if isinstance(item, dict) and item.get("source") in ("question", "context_question", "context_answer")
                else schema["properties"]["evidence"]["items"] for item in pool]
    _validate_structure(draft, schema)
    pool, used = draft["evidence"], set()
    result = {"contract_version": EVALUATION_VERSION, "applicability": draft["applicability"], "reason": draft["reason"],
              "criteria": {}, "discrepancies": deepcopy(draft["discrepancies"])}
    for key, item in draft["criteria"].items():
        ids = item["evidence_ids"]
        if any(type(i) is not int or not 0 <= i < len(pool) for i in ids):
            raise EvaluationContractError("referencia_evidencia_invalida", f"/criteria/{key}/evidence_ids", "evidence_reference", "Los índices deben identificar citas existentes y ser enteros.")
        used.update(ids)
        result["criteria"][key] = {"level": item["level"], "evidence": [deepcopy(pool[i]) for i in ids],
                                   "reason": item["reason"], "suggestion": None, "reformulation": None}
    if used != set(range(len(pool))):
        raise EvaluationContractError("evidencia_sin_referencia", "/evidence", "evidence_usage", "Cada cita debe sustentar al menos un criterio.")
    feedback = draft["feedback"]
    key = feedback["criterion"]
    if key is None:
        if feedback["suggestion"] is not None or feedback["reformulation"] is not None:
            raise EvaluationContractError("sugerencia_sin_criterio", "/feedback/criterion", "feedback_criterion", "Una sugerencia o reformulación requiere un criterio observado.")
    else:
        if result["criteria"][key]["level"] not in (1, 2, 3):
            raise EvaluationContractError("sugerencia_sin_defecto_observado", "/feedback/criterion", "observed_deficit", "El criterio de feedback debe tener un nivel observado entre 1 y 3.")
        result["criteria"][key].update(suggestion=feedback["suggestion"], reformulation=feedback["reformulation"])
    # Validar procedencia en el pool original para conservar su ruta de salida.
    for index, item in enumerate(pool):
        _validate_evidence(item, request, f"/evidence/{index}")
    return validate_draft(result, request)


def _validate_evidence(item, request, path):
    contexts = {t["turn_number"]: t for t in request["context_turns"]}
    if item["source"] == "question":
        if item["turn_number"] is not None:
            raise EvaluationContractError("contexto_invalido", path + "/turn_number", "question_turn", "La pregunta actual requiere turn_number=null.")
        source = request["question"]
    else:
        if type(item["turn_number"]) is not int or item["turn_number"] not in contexts:
            raise EvaluationContractError("contexto_invalido", path + "/turn_number", "authorized_context", "Usa exclusivamente un número de turno presente en context_turns.")
        source = contexts[item["turn_number"]]["question" if item["source"] == "context_question" else "answer"]
    if item["quote"] not in source:
        raise EvaluationContractError("cita_no_literal", path + "/quote", "literal_quote", "La cita debe ser una subcadena literal de la fuente indicada.")


def validate_draft(draft, request):
    """Las citas verifican procedencia, no certifican la interpretación semántica."""
    version = draft.get("contract_version") if isinstance(draft, dict) else None
    if version not in {"1.0.0", "1.1.0", EVALUATION_VERSION}:
        raise EvaluationContractError("contrato_invalido", "/contract_version", "enum", "La versión debe estar admitida por el evaluador.")
    _validate_structure(draft, analysis_schema(version))
    for key, criterion in draft["criteria"].items():
        path = f"/criteria/{key}"
        level, evidence = criterion["level"], criterion["evidence"]
        # jsonschema acepta 3.0 como integer; el contrato operativo exige int.
        if level is not None and type(level) is not int:
            raise EvaluationContractError("nivel_invalido", path + "/level", "integer_level", "El nivel observado debe ser un entero entre 1 y 4.")
        if level is not None and not evidence:
            raise EvaluationContractError("evidencia_ausente", path + "/evidence", "observed_evidence", "Un criterio puntuado requiere al menos una cita literal.")
        if level is None and (evidence or criterion["suggestion"] is not None or criterion["reformulation"] is not None):
            raise EvaluationContractError("criterio_insuficiente_incoherente", path, "missing_criterion", "Un nivel null requiere evidencia vacía y feedback null.")
        if version == "1.0.0" and level is not None and level < 4 and criterion["suggestion"] is None:
            raise EvaluationContractError("sugerencia_ausente", path + "/suggestion", "legacy_suggestion", "El protocolo 1.0 exige sugerencia para un criterio inferior a 4.")
        for index, item in enumerate(evidence):
            _validate_evidence(item, request, path + f"/evidence/{index}")
    if draft["applicability"] == "no_evaluable" and any(c["level"] is not None for c in draft["criteria"].values()):
        raise EvaluationContractError("no_evaluable_con_puntuacion", "/applicability", "no_evaluable_levels", "Una intervención no evaluable requiere todos los niveles null.")
    fields = [d["field"] for d in draft["discrepancies"]]
    if len(fields) != len(set(fields)):
        raise EvaluationContractError("discrepancia_duplicada", "/discrepancies", "unique_fields", "No repitas campos en las discrepancias.")
    if draft["discrepancies"] and request["classification"] is None:
        raise EvaluationContractError("discrepancia_sin_clasificacion", "/discrepancies", "classification_required", "Una discrepancia requiere clasificación auxiliar disponible.")
    for index, item in enumerate(draft["discrepancies"]):
        if item["quote"] not in request["question"]:
            raise EvaluationContractError("cita_no_literal", f"/discrepancies/{index}/quote", "literal_quote", "La cita debe ser literal en la pregunta actual.")
    return deepcopy(draft)


def evaluator_few_shot_schema():
    nullable_hash = {"anyOf": [{"type": "null"}, {"type": "string", "pattern": "^[a-f0-9]{64}$"}]}
    return _object({"enabled": {"type": "boolean"}, "version": {"const": "1.0.0"},
                    "case_ids": {"type": "array", "maxItems": 6, "uniqueItems": True, "items": {"enum": list(DEMONSTRATION_CASES)}},
                    "reference_sha256": deepcopy(nullable_hash), "examples_sha256": deepcopy(nullable_hash),
                    "job_sha256": deepcopy(nullable_hash),
                    "reason": {"enum": ["active", "disabled_by_option", "rubric_incompatible", "job_incompatible"]}})


def evaluation_record_schema():
    nullable_text = {"anyOf": [{"type": "null"}, _text(1000)]}
    nullable_number = {"type": ["number", "null"], "minimum": 0, "maximum": 100}
    schema = _object({
        "evaluation_version": {"enum": ["1.0.0", "1.1.0", EVALUATION_VERSION, RECORD_VERSION]}, "evaluation_id": _text(100),
        "few_shot": evaluator_few_shot_schema(),
        "method": {"enum": ["llm_python", "policy", "unavailable"]},
        "session_id": _text(100), "intervention_id": _text(100),
        "question_number": {"type": ["integer", "null"], "minimum": 1, "maximum": 20},
        "status": {"enum": ["evaluada", "parcial", "no_evaluable", "no_ejecutada", "no_disponible"]},
        "reason_code": _text(80), "request": evaluation_request_schema(),
        "analysis": {"anyOf": [{"type": "null"}, analysis_schema("1.0.0"), analysis_schema("1.1.0"), analysis_schema(EVALUATION_VERSION)]},
        "weighted_score": {"type": ["number", "null"], "minimum": 1, "maximum": 4},
        "normalized_score": nullable_number,
        "visible_level": {"enum": [None, *LEVELS]}, "critical_cap_applied": {"type": "boolean"},
        "explanation": _text(1000), "suggestion": nullable_text, "reformulation": nullable_text,
        "discrepancies": {"type": "array", "items": {"type": "object"}},
        "attempts": {"type": "array", "maxItems": 2, "items": _object({
            "number": {"type": "integer", "minimum": 1, "maximum": 2}, "status": {"enum": ["validada", "json_invalido", "contrato_invalido", "error_proveedor", "salida_incompleta"]},
            "error_code": {"type": ["string", "null"]},
            "validation": {"anyOf": [{"type": "null"}, _object({"path": _text(250), "rule": _text(80), "message": _text(500)})]},
            "input_tokens": {"type": ["integer", "null"], "minimum": 0},
            "output_tokens": {"type": ["integer", "null"], "minimum": 0},
            "elapsed_seconds": {"type": ["number", "null"], "minimum": 0},
            "provider": {"type": ["string", "null"]}, "model": {"type": ["string", "null"]}})},
        "elapsed_seconds": {"type": "number", "minimum": 0}, "prompt_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    })
    attempt = schema["properties"]["attempts"]["items"]
    attempt["required"].remove("validation")  # Los registros antiguos no tenían este campo.
    schema["required"].remove("few_shot")
    schema["allOf"] = [{"if": {"properties": {"evaluation_version": {"enum": [EVALUATION_VERSION, RECORD_VERSION]}}},
                         "then": {"properties": {"attempts": {"items": {"required": ["validation"]}}}}},
                        {"if": {"properties": {"evaluation_version": {"const": RECORD_VERSION}}},
                         "then": {"required": ["few_shot"]}}]
    return schema


def evaluation_request_schema():
    context = _object({"turn_number": {"type": "integer", "minimum": 1, "maximum": 20},
                       "question": {"type": "string"}, "answer": _text(4000), "truncated": {"type": "boolean"}})
    hint = _object({"evaluability": {"enum": [None, "evaluable", "no_evaluable"]},
                    "technical_error": {"type": ["string", "null"]},
                    "labels": {"type": ["object", "null"]}})
    return _object({"question": {"type": "string"}, "configuration": {"type": "object"},
                    "job": {"type": "object", "required": ["job_id"]},
                    "competency": {"type": ["string", "null"]}, "objective": {"type": ["string", "null"]},
                    "context_turns": {"type": "array", "maxItems": 10, "items": context},
                    "classification": {"anyOf": [{"type": "null"}, hint]}})


def validate_record(record, rubric):
    rubric = validate_rubric(rubric)
    if not Draft202012Validator(evaluation_record_schema()).is_valid(record):
        raise ValueError("Registro de evaluación inválido.")
    analysis = record["analysis"]
    metadata = record.get("few_shot")
    if metadata is not None:
        hashes = [metadata[k] for k in ("reference_sha256", "examples_sha256", "job_sha256")]
        if metadata["enabled"]:
            if (metadata["case_ids"] != list(DEMONSTRATION_CASES) or metadata["reason"] != "active"
                    or any(h is None for h in hashes)):
                raise ValueError("Procedencia de demostraciones incoherente.")
        elif metadata["case_ids"] or any(h is not None for h in hashes) or metadata["reason"] == "active":
            raise ValueError("Una evaluación sin ejemplos no admite demostraciones activas.")
    expected_method = "llm_python" if analysis is not None else "policy" if record["status"] in {"no_ejecutada", "no_evaluable"} else "unavailable"
    if record["method"] != expected_method:
        raise ValueError("Procedencia de evaluación incompatible.")
    if analysis is not None:
        expected_version = EVALUATION_VERSION if record["evaluation_version"] == RECORD_VERSION else record["evaluation_version"]
        if expected_version != analysis["contract_version"]:
            raise ValueError("La versión de análisis no coincide con el evaluador.")
        validate_draft(analysis, record["request"])
        expected = score_criteria({k: analysis["criteria"][k]["level"] for k in CRITERIA}, rubric)
        if analysis["applicability"] == "no_evaluable":
            status = "no_evaluable"
        elif expected["visible_level"] is not None:
            status = "evaluada"
        elif any(c["level"] is not None for c in analysis["criteria"].values()):
            status = "parcial"
        else:
            status = "no_disponible"
        if record["status"] != status or any(record[k] != v for k, v in expected.items()):
            raise ValueError("La puntuación o estado no corresponden a las evidencias.")
        hint = record["request"]["classification"]
        discrepancies = []
        for item in analysis["discrepancies"]:
            original = hint["evaluability"] if item["field"] == "evaluability" else None if hint["labels"] is None else hint["labels"].get(item["field"])
            discrepancies.append({**item, "original": original, "review_status": "pending"})
        if record["discrepancies"] != discrepancies:
            raise ValueError("Discrepancias derivadas incompatibles con el análisis.")
        from harness.feedback import build_feedback
        feedback = build_feedback(analysis, expected, rubric)
        if any(record[k] != v for k, v in feedback.items()):
            raise ValueError("La retroalimentación no corresponde al análisis validado.")
    elif (record["status"] not in {"no_evaluable", "no_ejecutada", "no_disponible"}
          or any(record[k] is not None for k in ("weighted_score", "normalized_score", "visible_level"))
          or record["critical_cap_applied"] or record["discrepancies"]):
        raise ValueError("Un registro sin análisis no admite calificación.")
    attempts = record["attempts"]
    for attempt in attempts:
        validation = attempt.get("validation")
        if record["evaluation_version"] in {EVALUATION_VERSION, RECORD_VERSION}:
            if (attempt["status"] == "contrato_invalido") != (validation is not None):
                raise ValueError("El diagnóstico no coincide con el estado del intento.")
        if validation is not None and (attempt["status"] != "contrato_invalido" or not attempt["error_code"]):
            raise ValueError("Un diagnóstico requiere un rechazo de contrato identificado.")
    if [a["number"] for a in attempts] != list(range(1, len(attempts) + 1)):
        raise ValueError("Intentos fuera de orden.")
    if len(attempts) == 2 and attempts[0]["status"] not in {"json_invalido", "contrato_invalido"}:
        raise ValueError("Reintento no autorizado.")
    if (analysis is not None) != bool(attempts and attempts[-1]["status"] == "validada"):
        raise ValueError("El análisis no coincide con el estado de los intentos.")
    return deepcopy(record)

"""Medir referencias aprobadas sin ajustar etiquetas ni invocar modelos."""

from collections import Counter
from copy import deepcopy

from harness.classification_contract import (
    ClassificationContractError, classification_expectation_schema, validate_classification,
)


EVALUATION_VERSION = "1.1.0"
LABEL_FIELDS = ("approaches", "main_approach", "secondary_approaches", "forms", "main_form", "attributes", "certainty")
UNIT_FIELDS = ("unit_id", "text", "source_start", "source_end", "context_status", "followup_of", "depends_on")
MISSING = {"abstencion": "__abstencion__", "respaldo_tecnico": "__error_tecnico__",
           "resultado_invalido": "__resultado_invalido__"}


def fraction(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def operation_metrics(attempts):
    """Sumar medidas informadas; no convertir consumo desconocido en cero."""
    result = {"generations": len(attempts)}
    for field in ("input_tokens", "output_tokens", "elapsed_seconds"):
        values = [a[field] for a in attempts if a.get(field) is not None]
        result[field] = {"known_total": sum(values) if values or not attempts else None,
                         "reported_generations": len(values), "total_generations": len(attempts)}
    return result


def _labels(data):
    if data is None:
        return None
    return {key: sorted(data[key]) if isinstance(data[key], list) else data[key] for key in LABEL_FIELDS}


def semantic_projection(result):
    """Excluir prosa y procedencia; los conjuntos de etiquetas no tienen orden."""
    return {"evaluability": result["evaluability"], "non_evaluable_reason": result["non_evaluable_reason"],
            "classification": _labels(result["classification"]),
            "context_turn_ids": sorted(result["context_turn_ids"]),
            "units": [{**{key: unit[key] for key in UNIT_FIELDS}, "classification": _labels(unit["classification"])}
                      for unit in result["units"]]}


def unit_comparison(expected, obtained):
    """Separar cobertura literal y etiquetas, sin atribuir acierto por coherencia.

    Etiquetas solo comparables cuando las unidades literales coinciden.
    Sin predicción o sin unidades evaluables esperadas, no inventar un acierto.
    """
    if obtained is None or expected["evaluability"] != "evaluable":
        return {"segmentation_exact": None, "unit_labels_exact": None}
    def spans(result):
        return [(u["text"], u["source_start"], u["source_end"]) for u in result["units"]]
    same = spans(expected) == spans(obtained)
    return {"segmentation_exact": same, "unit_labels_exact": (
        [_labels(u["classification"]) for u in expected["units"]] ==
        [_labels(u["classification"]) for u in obtained["units"]]) if same else None}


def _differences(expected, obtained, path=""):
    if isinstance(expected, dict) and isinstance(obtained, dict):
        return [diff for key in expected for diff in _differences(expected[key], obtained.get(key), f"{path}/{key}")]
    if isinstance(expected, list) and isinstance(obtained, list) and len(expected) == len(obtained):
        return [diff for i, (left, right) in enumerate(zip(expected, obtained))
                for diff in _differences(left, right, f"{path}/{i}")]
    return [] if expected == obtained else [{"path": path, "expected": expected, "obtained": obtained}]


def assess_case(case, request, observation):
    """Revalidar un resultado contra su entrada; guardar diferencias revisables.

    observation es LocalDecision.to_dict o HybridClassification.to_dict del
    programa. Una salida inválida no se conserva como clasificación aceptada.
    Las trazas aceptadas ya excluyen cuerpos y errores libres del proveedor.
    """
    raw = deepcopy(observation)
    hybrid = "trace" in raw
    local = raw["trace"]["local"] if hybrid else raw
    llm = raw["trace"]["llm"] if hybrid else None
    attempts = [] if llm is None else deepcopy(llm["attempts"])
    prediction = None
    outcome = "abstencion"
    if raw.get("result") is not None:
        try:
            prediction = validate_classification(raw["result"], expected_intervention_id=request["intervention_id"],
                expected_text=request["text"], allowed_context_turn_ids=tuple(t["turn_number"] for t in request["context_turns"]))
        except ClassificationContractError:
            outcome = "resultado_invalido"
            # No conservar un objeto rechazado, aunque alegue estar validado.
            raw = None
        else:
            outcome = "respaldo_tecnico" if prediction["technical_error"] is not None else "clasificada"
    elif hybrid or local.get("status") != "abstencion":
        outcome = "resultado_invalido"
        raw = None
    differences = (_differences(semantic_projection(case["expected"]), semantic_projection(prediction))
                   if outcome == "clasificada" else [{"path": "/execution", "expected": "clasificada", "obtained": outcome}])
    entry = {"case_id": case["case_id"], "split": case["split"], "input": deepcopy(request),
             "expected": deepcopy(case["expected"]), "observation": raw, "prediction": prediction,
             "outcome": outcome, "local_abstained": local["status"] == "abstencion",
             "llm_delegated": hybrid and observation["route"] == "llm", "llm_attempts": attempts,
             "operation": operation_metrics(attempts),
             "differences": differences, "exact_semantic_match": not differences, "discrepancy": None,
             **unit_comparison(case["expected"], prediction if outcome == "clasificada" else None)}
    if differences:
        method = prediction["method"] if prediction is not None else None
        if outcome == "abstencion":
            categories = ["abstencion_local"]
        elif outcome == "resultado_invalido":
            categories = ["integracion_sistema"]
        elif outcome == "respaldo_tecnico":
            categories = ["proveedor_llm" if prediction["technical_error"] == "error_proveedor" else "validacion_json"]
        else:
            categories = ["regla_local" if method == "reglas" else "interpretacion_llm"]
            if any(d["path"] == "/units" or (d["path"].startswith("/units/") and
                    "/classification/" not in d["path"] and "context" not in d["path"] and
                    "followup_of" not in d["path"]) for d in differences):
                categories.append("segmentacion_subpreguntas")
            if any("context" in d["path"] or "followup" in d["path"] for d in differences):
                categories.append("uso_contexto")
        entry["discrepancy"] = {"case_id": case["case_id"], "text": request["text"],
            "context": deepcopy(request["context_turns"]), "expected": deepcopy(case["expected"]),
            "obtained": deepcopy(prediction), "method": method, "outcome": outcome,
            "categories": categories, "differences": deepcopy(differences),
            "rationale_produced": prediction["rationale"] if prediction else local.get("reason"),
            "possible_cause": "Hipótesis pendiente de revisión humana; la procedencia y las diferencias no prueban la causa.",
            "corrective_action": "Revisar definición, contexto y segmentación antes de proponer cambios versionados; conservar la referencia aprobada.",
            "review_status": "pending_human_review"}
    return entry


def _prf(tp, fp, fn):
    return {"tp": tp, "fp": fp, "fn": fn, "support": tp + fn, "predicted_positive": tp + fp,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def _averages(per_label):
    active = [name for name, row in per_label.items() if row["f1"] is not None]
    return {"macro_f1": sum(per_label[name]["f1"] for name in active) / len(active) if active else None,
            "macro_labels": active, "micro": _prf(*(sum(row[k] for row in per_label.values()) for k in ("tp", "fp", "fn")))}


def exclusive_metrics(expected, obtained, labels):
    """Errores/abstenciones son columnas de ausencia, nunca clases semánticas."""
    if len(expected) != len(obtained):
        raise ValueError("Las referencias y las predicciones deben tener la misma longitud.")
    per_label = {label: _prf(sum(e == p == label for e, p in zip(expected, obtained)),
                            sum(e != label and p == label for e, p in zip(expected, obtained)),
                            sum(e == label and p != label for e, p in zip(expected, obtained))) for label in labels}
    columns = list(labels) + sorted(set(obtained) - set(labels))
    return {"n": len(expected), "accuracy": fraction(sum(e == p for e, p in zip(expected, obtained)), len(expected)),
            "per_label": per_label, **_averages(per_label),
            "confusion": {"row_labels": list(labels), "column_labels": columns,
                "matrix": [[sum(e == row and p == column for e, p in zip(expected, obtained))
                            for column in columns] for row in labels]}}


def multilabel_metrics(expected, obtained, labels):
    """None significa ausencia de predicción; también falla el conjunto vacío."""
    if len(expected) != len(obtained):
        raise ValueError("Las referencias y las predicciones deben tener la misma longitud.")
    per_label = {label: _prf(sum(label in e and p is not None and label in p for e, p in zip(expected, obtained)),
                            sum(label not in e and p is not None and label in p for e, p in zip(expected, obtained)),
                            sum(label in e and (p is None or label not in p) for e, p in zip(expected, obtained)))
                 for label in labels}
    return {"n": len(expected), "exact_set_match": fraction(sum(p is not None and set(e) == set(p)
                for e, p in zip(expected, obtained)), len(expected)), "per_label": per_label, **_averages(per_label),
            "missing_predictions": sum(p is None for p in obtained)}


def summarize_cases(entries):
    """Dimensiones y denominadores separados, incluyendo fallos y abstenciones."""
    n = len(entries)
    schema = classification_expectation_schema()
    approaches = schema["$defs"]["approach"]["enum"]
    forms = schema["$defs"]["form"]["enum"]
    label_schema = schema["$defs"]["classification"]["properties"]
    evaluable = [e for e in entries if e["expected"]["evaluability"] == "evaluable"]
    classified = [e for e in entries if e["outcome"] == "clasificada"]

    def obtained(entry, field=None):
        if entry["outcome"] != "clasificada":
            return MISSING[entry["outcome"]]
        result = entry["prediction"]
        if field is None:
            return result["evaluability"]
        if result["evaluability"] != "evaluable":
            return "__no_evaluable__"
        return result["classification"][field] or "__sin_principal__"

    exclusive = {"evaluability": exclusive_metrics([e["expected"]["evaluability"] for e in entries],
                  [obtained(e) for e in entries], ["evaluable", "no_evaluable"])}
    for field, labels in (("main_approach", approaches + ["__sin_principal__"]),
                          ("main_form", forms + ["__sin_principal__"]),
                          ("certainty", label_schema["certainty"]["enum"])):
        exclusive[field] = exclusive_metrics([e["expected"]["classification"][field] or "__sin_principal__" for e in evaluable],
                                            [obtained(e, field) for e in evaluable], labels)
    multilabel = {}
    for field, labels in (("approaches", approaches), ("forms", forms),
                          ("attributes", label_schema["attributes"]["items"]["enum"])):
        multilabel[field] = multilabel_metrics([e["expected"]["classification"][field] for e in evaluable],
            [e["prediction"]["classification"][field] if e["outcome"] == "clasificada"
             and e["prediction"]["evaluability"] == "evaluable" else None for e in evaluable], labels)
    attempts = [a for e in entries for a in e["llm_attempts"]]
    statuses = Counter(a["status"] for a in attempts)
    incorrect_structured = statuses["json_invalido"] + statuses["contrato_invalido"]
    unit_checks = [unit_comparison(e["expected"], e["prediction"]) for e in classified]
    def unit_metric(field):
        values = [item[field] for item in unit_checks if item[field] is not None]
        return fraction(sum(values), len(values))
    return {"n": n, "classified": len(classified), "outcomes": dict(Counter(e["outcome"] for e in entries)),
            "semantic_exact_all": fraction(sum(e["exact_semantic_match"] for e in entries), n),
            "semantic_exact_on_classified": fraction(sum(e["exact_semantic_match"] for e in classified), len(classified)),
            "segmentation_exact_on_classified_evaluable": unit_metric("segmentation_exact"),
            "unit_labels_exact_on_matching_segmentation": unit_metric("unit_labels_exact"),
            "exclusive": exclusive, "multilabel": multilabel,
            "local_abstention_rate": fraction(sum(e["local_abstained"] for e in entries), n),
            "llm_delegation_rate": fraction(sum(e["llm_delegated"] for e in entries), n),
            "technical_fallback_rate": fraction(sum(e["outcome"] == "respaldo_tecnico" for e in entries), n),
            "invalid_result_rate": fraction(sum(e["outcome"] == "resultado_invalido" for e in entries), n),
            "llm_generations": len(attempts), "llm_attempt_statuses": dict(statuses),
            "operation": operation_metrics(attempts),
            "invalid_json_generation_rate": fraction(statuses["json_invalido"], len(attempts)),
            "invalid_contract_generation_rate": fraction(statuses["contrato_invalido"], len(attempts)),
            "invalid_structured_generation_rate": fraction(incorrect_structured, len(attempts)),
            "repaired_cases": sum(len(e["llm_attempts"]) == 2 and e["llm_attempts"][0]["status"] in
                 {"json_invalido", "contrato_invalido"} and e["llm_attempts"][-1]["status"] == "validada" for e in entries),
            "discrepancy_cases": sum(e["discrepancy"] is not None for e in entries)}


def grouped_metrics(entries):
    return {"all": summarize_cases(entries), **{split: summarize_cases([e for e in entries if e["split"] == split])
            for split in ("desarrollo", "comprobacion_conocida")}}

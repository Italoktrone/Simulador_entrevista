"""Referencias educativas independientes de las etiquetas del clasificador."""

from copy import deepcopy
from pathlib import Path

from harness.json_loader import load_json
from harness.scoring import CRITERIA, load_rubric, score_criteria

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "data/reference_questions/evaluacion_calidad_aprobada.json"


def load_quality_references(path=REFERENCE_PATH, *, rubric=None):
    data = load_json(path)
    if rubric is None:
        rubric = load_rubric(ROOT / "config/evaluation.legacy-1.0.0.json") if isinstance(data, dict) and data.get("rubric_version") == "1.0.0" else load_rubric()
    if (not isinstance(data, dict) or data.get("suite_version") != "1.0.0"
            or data.get("rubric_version") != rubric["rubric_version"] or not isinstance(data.get("cases"), list)):
        raise ValueError("Conjunto de referencias incompatible con la rúbrica.")
    seen = set()
    for case in data["cases"]:
        required = {"case_id", "question", "approach", "objective", "competency", "context_turns", "classification",
                    "difficulty", "split", "review_status", "reviewer", "expected"}
        if (not isinstance(case, dict) or set(case) != required or not isinstance(case["case_id"], str)
                or not case["case_id"] or case["case_id"] in seen or not isinstance(case["question"], str)
                or case["approach"] not in {"conductual", "situacional", "mixto"}
                or case["split"] not in {"desarrollo", "comprobacion_conocida"}
                or case["review_status"] not in {"pending", "approved"}
                or not isinstance(case["context_turns"], list)):
            raise ValueError("Caso de referencia inválido o repetido.")
        seen.add(case["case_id"])
        if case["review_status"] == "approved" and (not isinstance(case["reviewer"], str) or not case["reviewer"].strip()):
            raise ValueError("Una referencia aprobada requiere identificar a quien la revisó.")
        expected = case["expected"]
        if not isinstance(expected, dict) or set(expected) != {"levels", "status", "visible_level", "justifications"}:
            raise ValueError("Resultado esperado incompleto.")
        score = score_criteria(expected["levels"], rubric)
        if (not isinstance(expected["justifications"], dict) or set(expected["justifications"]) != set(CRITERIA)
                or any(not isinstance(s, str) or not s.strip() for s in expected["justifications"].values())):
            raise ValueError("Se necesitan justificaciones para los cuatro criterios.")
        status = "evaluada" if score["visible_level"] else "parcial" if any(v is not None for v in expected["levels"].values()) else "no_disponible"
        if expected["status"] == "no_evaluable" and all(v is None for v in expected["levels"].values()):
            status = "no_evaluable"
        if expected["status"] != status or expected["visible_level"] != score["visible_level"]:
            raise ValueError("El resultado global esperado no corresponde a sus niveles y rúbrica.")
    return deepcopy(data)


def compare_quality(expected, record):
    obtained = None if record["analysis"] is None else {k: record["analysis"]["criteria"][k]["level"] for k in CRITERIA}
    differences = []
    if obtained is None and record["status"] == "no_disponible":
        differences.append({"field": "execution", "expected": "analisis_valido", "obtained": record["reason_code"], "review_status": "pending"})
    for key in ("status", "visible_level"):
        if expected[key] != record[key]:
            differences.append({"field": key, "expected": expected[key], "obtained": record[key], "review_status": "pending"})
    for key in CRITERIA:
        value = None if obtained is None else obtained[key]
        if value != expected["levels"][key]:
            differences.append({"field": key, "expected": expected["levels"][key], "obtained": value, "review_status": "pending"})
    return {"exact": not differences, "differences": differences}


def quality_metrics(cases):
    """Cobertura explícita; una ausencia no se cuenta como acierto o error ordinal cero."""
    by_criterion = {}
    for key in CRITERIA:
        pairs = []
        expected_observed = 0
        for case in cases:
            expected = case["expected"]["levels"][key]
            expected_observed += expected is not None
            analysis = case["record"]["analysis"]
            actual = None if analysis is None else analysis["criteria"][key]["level"]
            if expected is not None and actual is not None:
                pairs.append((expected, actual))
        by_criterion[key] = {
            "expected_observed": expected_observed, "compared": len(pairs),
            "missing_prediction": expected_observed - len(pairs),
            "exact": sum(a == b for a, b in pairs),
            "mean_absolute_error": None if not pairs else sum(abs(a - b) for a, b in pairs) / len(pairs),
            "within_one_level": sum(abs(a - b) <= 1 for a, b in pairs),
        }
    return {"cases": len(cases), "exact_all": sum(compare_quality(c["expected"], c["record"])["exact"] for c in cases),
            "available_global": sum(c["record"]["status"] == "evaluada" for c in cases),
            "unavailable": sum(c["record"]["status"] == "no_disponible" for c in cases), "criteria": by_criterion}

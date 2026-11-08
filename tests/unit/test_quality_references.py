"""Las propuestas pendientes no se convierten en referencias aprobadas al ejecutar."""

import json
import pytest

from harness.quality_references import load_quality_references, quality_metrics, compare_quality
from harness.question_evaluator import QuestionEvaluator
from harness.scoring import CRITERIA
from scripts import evaluate_questions
from tests.evaluation_fixtures import EvaluationClient
from tests.unit.test_question_evaluation import request, evaluate


def test_forty_approved_references_keep_split_and_reviewer():
    suite = load_quality_references()
    assert len(suite["cases"]) == 40
    assert all(c["review_status"] == "approved" and c["reviewer"] for c in suite["cases"])
    assert suite["reference_version"] == suite["rubric_version"] == "1.1.0"
    assert sum(c["split"] == "desarrollo" for c in suite["cases"]) == 30
    assert {c["expected"]["status"] for c in suite["cases"]} >= {"evaluada", "parcial", "no_evaluable"}


@pytest.mark.parametrize("preview", [True, False])
def test_pending_references_never_create_a_model_client(monkeypatch, tmp_path, preview):
    def forbidden(**kwargs):
        raise AssertionError("No debe crearse un cliente.")
    monkeypatch.setattr(evaluate_questions, "create_evaluation_client", forbidden)
    suite = load_quality_references()
    for case in suite["cases"]:
        case.update(review_status="pending", reviewer=None)
    path = tmp_path / "pending.json"
    path.write_text(json.dumps(suite), encoding="utf-8")
    assert evaluate_questions.main((["--preview"] if preview else []) + ["--case-id", "E01", "--references", str(path)]) == (0 if preview else 2)


def test_approval_requires_reviewer_and_does_not_change_references(tmp_path):
    suite = load_quality_references()
    suite["cases"][0]["review_status"] = "approved"
    suite["cases"][0]["reviewer"] = None
    path = tmp_path / "references.json"
    path.write_text(json.dumps(suite), encoding="utf-8")
    with pytest.raises(ValueError):
        load_quality_references(path)


def test_metrics_separate_missing_predictions_from_ordinal_errors():
    evaluator = QuestionEvaluator(EvaluationClient())
    record = evaluate(evaluator)
    expected = {"levels": dict.fromkeys(CRITERIA, 4), "status": "evaluada", "visible_level": "Destacado"}
    comparison = compare_quality(expected, record)
    assert not comparison["exact"] and len(comparison["differences"]) == 5
    missing = evaluator.unavailable(request(evaluator), session_id="sesion-test", intervention_id="sesion-test:i2")
    metrics = quality_metrics([{"expected": expected, "record": record}, {"expected": expected, "record": missing}])
    assert metrics["cases"] == 2 and metrics["unavailable"] == 1
    for values in metrics["criteria"].values():
        assert values["compared"] == values["missing_prediction"] == 1
        assert values["mean_absolute_error"] == 1

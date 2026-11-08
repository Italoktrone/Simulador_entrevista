"""Protocolo reducido: misma evidencia, sin inventar datos ni descartar notas por feedback ausente."""

import pytest

from harness.evaluation_contract import complete_evaluation, validate_draft, validate_record
from harness.feedback import format_feedback, build_feedback
from harness.question_evaluator import QuestionEvaluator
from tests.evaluation_fixtures import EvaluationClient, draft, compact
from tests.unit.test_question_evaluation import request, evaluate


def test_shared_literal_is_expanded_without_changing_levels():
    value = compact(draft())
    assert len(value["evidence"]) == 1
    evaluator = QuestionEvaluator(EvaluationClient())
    analysis = complete_evaluation(value, request(evaluator))
    assert {k: v["level"] for k, v in analysis["criteria"].items()} == dict.fromkeys(value["criteria"], 3)
    assert all(c["evidence"] == value["evidence"] for c in analysis["criteria"].values())


@pytest.mark.parametrize("level", [1, 2, 3])
def test_no_suggestions_does_not_discard_observed_levels_or_retry(level):
    source = draft(levels={"pertinencia": level, "enfoque": 4, "claridad": 4, "neutralidad": 4})
    for item in source["criteria"].values():
        item["suggestion"] = None
    client = EvaluationClient([source])
    result = evaluate(QuestionEvaluator(client))
    assert len(client.requests) == 1 and result["status"] == "evaluada"
    assert result["analysis"]["criteria"]["pertinencia"]["level"] == level
    assert result["suggestion"] and "Mantén la precisión" not in result["suggestion"]
    validate_record(result, QuestionEvaluator(EvaluationClient()).rubric)


@pytest.mark.parametrize("invalid_ids", [[3], [True], [0.0], [-1]])
def test_bad_evidence_references_are_not_normalized(invalid_ids):
    value = compact(draft())
    value["criteria"]["claridad"]["evidence_ids"] = invalid_ids
    evaluator = QuestionEvaluator(EvaluationClient())
    with pytest.raises(ValueError):
        complete_evaluation(value, request(evaluator))


def test_unused_quote_is_not_silently_dropped():
    value = compact(draft())
    value["evidence"].append({"source": "question", "turn_number": None, "quote": "CITA_INVENTADA"})
    evaluator = QuestionEvaluator(EvaluationClient())
    with pytest.raises(ValueError):
        complete_evaluation(value, request(evaluator))


def test_legacy_contract_still_requires_its_original_suggestions():
    value = draft()
    value["criteria"]["claridad"]["suggestion"] = None
    evaluator = QuestionEvaluator(EvaluationClient())
    with pytest.raises(ValueError, match="sugerencia_ausente"):
        validate_draft(value, request(evaluator))


def test_legacy_record_uses_its_original_validation_and_feedback():
    evaluator = QuestionEvaluator(EvaluationClient())
    record = evaluate(evaluator)
    record.update(evaluation_version="1.0.0", analysis=draft())
    record.update(build_feedback(record["analysis"], record, evaluator.rubric))
    assert validate_record(record, evaluator.rubric) == record


def test_timeout_is_visible_without_duplicate_generic_message():
    from harness.llm.client import LLMTimeoutError
    evaluator = QuestionEvaluator(EvaluationClient([LLMTimeoutError("privado")]))
    result = evaluate(evaluator)
    assert "tiempo de espera" in format_feedback(result)
    assert result["attempts"][0]["elapsed_seconds"] is not None
    assert result["normalized_score"] is None

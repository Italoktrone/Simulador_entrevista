"""Regla aprobada: límite visible, sin alterar aritmética ni archivos históricos."""

from itertools import product

import pytest

from harness.evaluation_contract import validate_record
from harness.quality_references import load_quality_references
from harness.scoring import CRITERIA, LEVELS, ROOT, load_rubric, score_criteria, validate_rubric
from harness.session_log import load_session
from harness.question_evaluator import QuestionEvaluator
from tests.evaluation_fixtures import EvaluationClient, draft
from tests.unit.test_question_evaluation import evaluate


@pytest.mark.parametrize("values", list(product(range(1, 5), repeat=4)))
def test_all_256_combinations_preserve_math_and_apply_cap(values):
    levels = dict(zip(CRITERIA, values))
    current = score_criteria(levels, load_rubric())
    old = load_rubric(ROOT / "config/evaluation.legacy-1.0.0.json")
    old["block_distinguished_on_level_one"] = False
    uncapped = score_criteria(levels, old)
    assert all(current[k] == uncapped[k] for k in ("weighted_score", "normalized_score"))
    expected = "En desarrollo" if 1 in values and LEVELS.index(uncapped["visible_level"]) > 1 else uncapped["visible_level"]
    assert current["visible_level"] == expected
    assert current["critical_cap_applied"] == (expected != uncapped["visible_level"])


@pytest.mark.parametrize("criterion", CRITERIA)
def test_zero_weight_cannot_bypass_a_critical_defect(criterion):
    rubric = load_rubric()
    rubric["weights"] = {k: 0 if k == criterion else (40 if k == next(x for x in CRITERIA if x != criterion) else 30) for k in CRITERIA}
    levels = dict.fromkeys(CRITERIA, 4)
    levels[criterion] = 1
    result = score_criteria(levels, rubric)
    assert result["normalized_score"] == 100 and result["visible_level"] == "En desarrollo"


def test_partial_stays_without_global_even_with_level_one():
    levels = dict(zip(CRITERIA, [1, None, 4, 4]))
    score = score_criteria(levels, load_rubric())
    assert score["visible_level"] is score["normalized_score"] is None


def test_legacy_rule_and_feedback_remain_replayable():
    rubric = load_rubric(ROOT / "config/evaluation.legacy-1.0.0.json")
    levels = dict(zip(CRITERIA, [4, 4, 4, 1]))
    evaluator = QuestionEvaluator(EvaluationClient([draft(levels=levels)]), rubric=rubric, few_shot=False)
    record = evaluate(evaluator)
    assert record["visible_level"] == "Logrado" and record["normalized_score"] == 85
    assert "No se asigna Destacado" in record["explanation"]
    validate_record(record, rubric)


def test_new_explanation_and_tampering_match_new_rule():
    levels = dict(zip(CRITERIA, [4, 4, 4, 1]))
    evaluator = QuestionEvaluator(EvaluationClient([draft(levels=levels)]))
    record = evaluate(evaluator)
    assert "se limita a En desarrollo" in record["explanation"] and "porcentaje se conserva" in record["explanation"]
    record["visible_level"] = "Logrado"
    with pytest.raises(ValueError, match="puntuación"):
        validate_record(record, evaluator.rubric)


@pytest.mark.parametrize("bad", [None, False, "Logrado", "Destacado"])
def test_approved_cap_cannot_be_disabled_in_rubric_11(bad):
    rubric = load_rubric()
    rubric["level_one_visible_cap"] = bad
    with pytest.raises(ValueError):
        validate_rubric(rubric)


def test_approval_preserves_all_questions_contexts_and_criterion_levels():
    proposed = load_quality_references(ROOT / "data/reference_questions/evaluacion_calidad_revision_propuesta.json")
    approved = load_quality_references()
    changed = []
    for before, after in zip(proposed["cases"], approved["cases"], strict=True):
        for key in ("question", "context_turns", "objective", "competency", "classification", "split"):
            assert before[key] == after[key]
        assert before["expected"]["levels"] == after["expected"]["levels"]
        assert before["expected"]["justifications"] == after["expected"]["justifications"]
        if before["expected"]["visible_level"] != after["expected"]["visible_level"]:
            changed.append(after["case_id"])
    assert changed == ["E09", "E10", "E12"]


def test_previous_real_session_keeps_its_original_rubric_and_bytes():
    path = ROOT / "outputs/sessions/session-a6616bd6-22de-4a22-8950-6315cc6931c2.json"
    if not path.exists():
        pytest.skip("Sesión manual no distribuida.")
    before = path.read_bytes()
    session = load_session(path)
    assert session["evaluation_policy"]["rubric_version"] == "1.0.0"
    assert path.read_bytes() == before

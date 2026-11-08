"""Puntuación, evidencia y recuperación sin red ni evaluación de modelos reales."""

from copy import deepcopy
import json

import httpx
import pytest

from harness.evaluation_contract import llm_evaluation_schema, evaluation_generation_schema, evaluation_record_schema, validate_draft, validate_record
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMTimeoutError, LLMResponse
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.scoring import CRITERIA, LEVELS, load_rubric, score_criteria, validate_rubric
from tests.evaluation_fixtures import EvaluationClient, draft, compact


def request(evaluator, question="¿Has utilizado Git?", **changes):
    setup = load_interview_setup()
    return evaluator.make_request(question=question, configuration=setup.config_dict(), job=setup.job_dict(), attempts=[], **changes)


def evaluate(evaluator, data=None):
    return evaluator.evaluate(request(evaluator) if data is None else data, session_id="sesion-test", intervention_id="sesion-test:i1", question_number=1)


@pytest.mark.parametrize("level,percent", [(1, 0), (2, 33.33), (3, 66.67), (4, 100)])
def test_anchors_preserve_levels(level, percent):
    result = score_criteria(dict.fromkeys(CRITERIA, level), load_rubric())
    assert result["normalized_score"] == percent
    assert result["visible_level"] == LEVELS[level - 1]


@pytest.mark.parametrize("threshold,expected", [(1.5, "En desarrollo"), (2.5, "Logrado"), (3.5, "Destacado")])
@pytest.mark.parametrize("delta,lower", [(0, False), (-0.000001, True), (0.000001, False)])
def test_thresholds_use_unrounded_average(threshold, expected, delta, lower):
    from harness.scoring import ROOT
    rubric = load_rubric(ROOT / "config/evaluation.legacy-1.0.0.json")
    rubric["block_distinguished_on_level_one"] = False
    from decimal import Decimal
    high_weight = float(Decimal(50) + Decimal(str(delta)) * 100)
    rubric["weights"] = dict(zip(CRITERIA, [high_weight, 100 - high_weight, 0, 0]))
    low = int(threshold - 0.5)
    result = score_criteria(dict(zip(CRITERIA, [low + 1, low, low, low])), rubric)
    assert result["visible_level"] == LEVELS[LEVELS.index(expected) - int(lower)]


def test_severe_defect_caps_distinguished_without_changing_math():
    result = score_criteria(dict(zip(CRITERIA, [4, 4, 4, 1])), load_rubric())
    assert result == {"weighted_score": 3.55, "normalized_score": 85, "visible_level": "En desarrollo", "critical_cap_applied": True}


@pytest.mark.parametrize("criterion", CRITERIA)
def test_missing_evidence_never_imputes_or_renormalizes(criterion):
    levels = dict.fromkeys(CRITERIA, 4)
    levels[criterion] = None
    result = score_criteria(levels, load_rubric())
    assert result["weighted_score"] is result["normalized_score"] is result["visible_level"] is None


@pytest.mark.parametrize("bad", [0, 5, True, False, 2.5, 3.0, "3", float("nan")])
def test_rejects_invalid_levels(bad):
    with pytest.raises(ValueError):
        score_criteria(dict.fromkeys(CRITERIA, bad), load_rubric())


@pytest.mark.parametrize("field,bad", [("weights", dict.fromkeys(CRITERIA, 20)), ("weights", dict.fromkeys(CRITERIA, True)),
    ("weights", dict(zip(CRITERIA, [-1, 31, 40, 30]))), ("thresholds", [1.5, 1.5, 3.5]),
    ("thresholds", [1, 2, 3]), ("thresholds", [2, 3, 4]), ("thresholds", [float("nan"), 2, 3]),
    ("read_timeout_seconds", 0), ("context_pairs", 0), ("max_output_tokens", 8192), ("descriptors", {}),
    ("level_one_visible_cap", "Logrado")])
def test_bad_config_is_rejected_not_repaired(field, bad):
    rubric = load_rubric()
    rubric[field] = bad
    with pytest.raises(ValueError):
        validate_rubric(rubric)


def test_draft_cannot_supply_derived_fields_or_float_levels():
    evaluator = QuestionEvaluator(EvaluationClient())
    data = request(evaluator)
    for key in ("visible_level", "normalized_score", "weights"):
        value = draft() | {key: "NO_AUTORIZADO"}
        with pytest.raises(ValueError):
            validate_draft(value, data)
    value = draft()
    value["criteria"]["claridad"]["level"] = 3.0
    with pytest.raises(ValueError):
        validate_draft(value, data)


@pytest.mark.parametrize("change", ["nonliteral", "future_context", "no_evidence"])
def test_invalid_evidence_or_contract_is_repaired_only_once(change):
    value = draft()
    item = value["criteria"]["claridad"]
    if change == "nonliteral":
        item["evidence"][0]["quote"] = "TEXTO_AUSENTE_PRIVADO"
    elif change == "future_context":
        item["evidence"][0].update(source="context_answer", turn_number=99)
    elif change == "no_evidence":
        item["evidence"] = []
    client = EvaluationClient([value, value])
    evaluator = QuestionEvaluator(client)
    result = evaluate(evaluator)
    assert result["status"] == "no_disponible" and result["visible_level"] is None
    assert len(client.requests) == len(result["attempts"]) == 2
    assert "TEXTO_AUSENTE_PRIVADO" not in json.dumps(result)
    assert "TEXTO_AUSENTE_PRIVADO" not in client.requests[-1][0]["content"]


def test_repair_can_recover_and_keeps_math_in_python():
    client = EvaluationClient(["JSON_RECHAZADO_PRIVADO", draft()])
    result = evaluate(QuestionEvaluator(client))
    assert result["status"] == "evaluada" and result["visible_level"] == "Logrado"
    assert result["normalized_score"] == 66.67
    assert "JSON_RECHAZADO_PRIVADO" not in json.dumps(result) + client.requests[-1][0]["content"]


def test_partial_preserves_observed_results_without_global_grade():
    value = draft(levels=dict(zip(CRITERIA, [3, None, 4, 4])))
    result = evaluate(QuestionEvaluator(EvaluationClient([value])))
    assert result["status"] == "parcial" and result["visible_level"] is None
    assert result["analysis"]["criteria"]["claridad"]["level"] == 4


def test_all_missing_is_unavailable_and_not_initial():
    value = draft(levels=dict.fromkeys(CRITERIA, None))
    result = evaluate(QuestionEvaluator(EvaluationClient([value])))
    assert result["status"] == "no_disponible" and result["normalized_score"] is None


def test_true_non_evaluable_is_distinct_from_failure():
    value = draft("Hola", dict.fromkeys(CRITERIA, None))
    value["applicability"] = "no_evaluable"
    evaluator = QuestionEvaluator(EvaluationClient([value]))
    result = evaluate(evaluator, request(evaluator, "Hola"))
    assert result["status"] == "no_evaluable" and result["visible_level"] is None


@pytest.mark.parametrize("outcome", [LLMTimeoutError("CLAVE_PRIVADA"), LLMResponse("corte", "modelo", "ollama", 1, finish_reason="length")])
def test_provider_failure_or_truncation_does_not_retry(outcome):
    client = EvaluationClient([outcome])
    result = evaluate(QuestionEvaluator(client))
    assert len(client.requests) == 1 and result["status"] == "no_disponible"
    assert "CLAVE_PRIVADA" not in json.dumps(result)


def test_literal_context_evidence_can_use_only_authorized_turn():
    evaluator = QuestionEvaluator(EvaluationClient())
    data = request(evaluator)
    data["context_turns"] = [{"turn_number": 2, "question": "¿Qué ocurrió?", "answer": "Corregí el error.", "truncated": False}]
    value = draft()
    value["criteria"]["claridad"]["evidence"] = [{"source": "context_answer", "turn_number": 2, "quote": "Corregí el error."}]
    assert validate_draft(value, data) == value


def test_classification_disagreement_is_logged_without_rewriting_original():
    evaluator = QuestionEvaluator(EvaluationClient())
    hint = {"evaluability": "evaluable", "classification": {"approaches": ["situacional"], "forms": ["cerrada"], "attributes": ["directiva"], "certainty": "clara"}, "technical_error": None}
    before = deepcopy(hint)
    data = request(evaluator, classification=hint)
    value = draft()
    value["discrepancies"] = [{"field": "attributes", "alternative": "Sin inducción observada", "reason": "La pregunta permite contestar libremente.", "quote": "¿Has utilizado Git?"}]
    evaluator._client = EvaluationClient([value])
    result = evaluate(evaluator, data)
    assert hint == before and result["discrepancies"][0]["original"] == ["directiva"]
    assert result["discrepancies"][0]["review_status"] == "pending"


def test_tampered_calculation_is_rejected():
    evaluator = QuestionEvaluator(EvaluationClient())
    value = evaluate(evaluator)
    value["visible_level"] = "Destacado"
    with pytest.raises(ValueError):
        validate_record(value, evaluator.rubric)


@pytest.mark.parametrize("provider", ["ollama", "unab", "openai"])
def test_client_has_independent_budget_wait_and_no_transport_retry(provider):
    env = {"LLM_PROVIDER": provider, "LLM_ALLOW_EXTERNAL_API": "true", "OLLAMA_MODEL": "modelo-local",
           "OPENAI_MODEL": "modelo-test", "OPENAI_API_KEY": "clave-test", "UNAB_API_KEY": "clave-test"}
    with create_evaluation_client(env, transport=httpx.MockTransport(lambda _: httpx.Response(500))) as client:
        assert client.settings.max_output_tokens == 2048
        assert client.settings.connection_retries == 0
        assert client.settings.read_timeout_seconds == client._http.timeout.read == 90


def test_exported_schemas_match_runtime_contracts():
    from harness.json_loader import load_json
    from harness.scoring import ROOT
    assert load_json(ROOT / "schemas/llm_question_evaluation.schema.json") == llm_evaluation_schema()
    assert load_json(ROOT / "schemas/question_evaluation.schema.json") == evaluation_record_schema()


@pytest.mark.parametrize("provider", ["ollama", "unab", "openai"])
def test_evaluator_uses_real_adapter_with_mock_http_and_provider_format(provider):
    calls = []
    value = json.dumps(compact(draft()))
    def handler(req):
        payload = json.loads(req.content)
        calls.append(payload)
        if provider == "ollama":
            assert payload["format"] == evaluation_generation_schema(allowed_context_turn_numbers=[], classification_available=False)
            assert payload["options"]["num_predict"] == 2048 and payload["options"]["temperature"] == 0
            body = {"model": "modelo", "done": True, "done_reason": "stop", "message": {"role": "assistant", "content": value}}
        elif provider == "unab":
            assert payload["max_tokens"] == 2048 and "format" not in payload
            body = {"model": "modelo", "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": value}}]}
        else:
            assert payload["max_output_tokens"] == 2048
            body = {"model": "modelo", "status": "completed", "output": [{"type": "message", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": value}]}]}
        return httpx.Response(200, json=body)
    env = {"LLM_PROVIDER": provider, "LLM_ALLOW_EXTERNAL_API": "true", "OLLAMA_MODEL": "modelo", "OPENAI_MODEL": "modelo", "OPENAI_API_KEY": "clave-test", "UNAB_API_KEY": "clave-test"}
    with create_evaluation_client(env, transport=httpx.MockTransport(handler)) as client:
        assert evaluate(QuestionEvaluator(client))["visible_level"] == "Logrado"
    assert len(calls) == 1

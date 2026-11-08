"""Regresiones de fallos reales: evidencia ausente y diagnóstico ambiguo."""

import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator

from harness.evaluation_contract import (
    llm_evaluation_schema, evaluation_generation_schema, validate_record,
)
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.session_log import load_session
from tests.evaluation_fixtures import EvaluationClient, compact, draft
from tests.unit.test_question_evaluation import evaluate, request


@pytest.mark.parametrize("level,ids,valid", [(3, [], False), (4, [0], True), (None, [], True), (None, [0], False)])
def test_native_grammar_requires_evidence_for_observed_level(level, ids, valid):
    schema = llm_evaluation_schema()
    validator = Draft202012Validator(schema).evolve(schema=schema["properties"]["criteria"]["properties"]["claridad"])
    assert validator.is_valid({"level": level, "evidence_ids": ids, "reason": "Criterio de prueba."}) is valid


@pytest.mark.parametrize("failure,path,rule", [
    ("absent", "/criteria/claridad/evidence_ids", "minItems"),
    ("length", "/criteria/enfoque/reason", "maxLength"),
    ("source", "/evidence/0/turn_number", "type"),
    ("extra", "/criteria/claridad", "additionalProperties"),
    ("quote", "/evidence/0/quote", "literal_quote"),
    ("index", "/criteria/claridad/evidence_ids", "evidence_reference"),
    ("context", "/evidence/0/turn_number", "authorized_context"),
])
def test_repair_names_the_actual_field_and_rule_without_rejected_values(failure, path, rule):
    value = compact(draft())
    if failure == "absent":
        value["criteria"]["claridad"]["evidence_ids"] = []
    elif failure == "length":
        value["criteria"]["enfoque"]["reason"] = "PRIVADO_" * 15
    elif failure == "source":
        value["evidence"][0]["turn_number"] = 1
    elif failure == "extra":
        value["criteria"]["claridad"]["token=PRIVADO"] = "PRIVADO"
    elif failure == "quote":
        value["evidence"][0]["quote"] = "PRIVADO"
    elif failure == "index":
        value["criteria"]["claridad"]["evidence_ids"] = [3]
    else:
        value["evidence"][0].update(source="context_answer", turn_number=17)
    client = EvaluationClient([value, draft()])
    result = evaluate(QuestionEvaluator(client))
    assert result["status"] == "evaluada" and len(client.requests) == 2
    audit = result["attempts"][0]["validation"]
    assert audit["path"] == path and audit["rule"] == rule
    if failure == "length":
        assert "110" in audit["message"]
    repair = client.requests[1][0]["content"]
    assert path in repair and rule in repair
    assert "PRIVADO" not in json.dumps(result) + repair
    assert result["attempts"][1]["validation"] is None


def test_oversized_literal_quote_reports_its_limit_without_trimming_it():
    question = "¿" + "información " * 15 + "?"
    value = compact(draft(question))
    value["evidence"][0]["quote"] = question
    client = EvaluationClient([value, value])
    evaluator = QuestionEvaluator(client)
    result = evaluate(evaluator, request(evaluator, question))
    assert result["analysis"] is None
    for item in result["attempts"]:
        assert item["validation"]["path"] == "/evidence/0/quote"
        assert item["validation"]["rule"] == "maxLength" and "160" in item["validation"]["message"]


def test_two_rejections_remain_ungraded_and_keep_both_diagnostics():
    value = compact(draft())
    value["criteria"]["claridad"]["evidence_ids"] = []
    client = EvaluationClient([value, value])
    result = evaluate(QuestionEvaluator(client))
    assert len(client.requests) == 2 and result["analysis"] is result["normalized_score"] is None
    assert all(a["validation"]["path"] == "/criteria/claridad/evidence_ids" for a in result["attempts"])
    result["attempts"][0]["validation"] = None
    with pytest.raises(ValueError, match="diagnóstico"):
        validate_record(result, QuestionEvaluator(EvaluationClient()).rubric)


def test_legacy_compact_record_keeps_original_feedback_without_new_audit():
    evaluator = QuestionEvaluator(EvaluationClient())
    record = evaluate(evaluator)
    record["evaluation_version"] = record["analysis"]["contract_version"] = "1.1.0"
    for item in record["attempts"]:
        del item["validation"]
    assert validate_record(record, evaluator.rubric) == record


def test_request_specific_native_schema_never_reuses_context_numbers():
    calls = []
    def handler(req):
        payload = json.loads(req.content)
        calls.append(payload["format"])
        return httpx.Response(200, json={"model": "modelo", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(compact(draft()))}})
    with create_evaluation_client({"LLM_PROVIDER": "ollama"}, transport=httpx.MockTransport(handler)) as client:
        evaluator = QuestionEvaluator(client)
        data = request(evaluator)
        data["context_turns"] = [{"turn_number": 7, "question": "¿Qué ocurrió?", "answer": "Corregí el error.", "truncated": False}]
        assert evaluate(evaluator, data)["status"] == "evaluada"
        assert evaluate(evaluator)["status"] == "evaluada"
    assert calls[0] == evaluation_generation_schema(allowed_context_turn_numbers=[7], classification_available=False)
    assert calls[1] == evaluation_generation_schema(allowed_context_turn_numbers=[], classification_available=False)
    assert not Draft202012Validator(calls[0]["properties"]["evidence"]["items"]).is_valid(
        {"source": "context_answer", "turn_number": 6, "quote": "Corregí el error."})


def test_native_text_length_is_not_overridden_by_pattern_and_python_remains_strict():
    schema = evaluation_generation_schema()
    bounded = []
    def collect(node):
        if isinstance(node, dict):
            if node.get("type") == "string" and "maxLength" in node:
                bounded.append(node)
            for child in node.values():
                collect(child)
        elif isinstance(node, list):
            for child in node:
                collect(child)
    collect(schema)
    assert bounded and all("pattern" not in node and node["minLength"] == 1 for node in bounded)
    value = compact(draft())
    value["criteria"]["claridad"]["reason"] = " "
    client = EvaluationClient([value, value])
    result = evaluate(QuestionEvaluator(client))
    assert result["analysis"] is None
    assert all(a["validation"]["rule"] == "pattern" for a in result["attempts"])


def test_old_session_with_unavailable_evaluations_is_read_without_changes():
    source = Path("outputs/sessions/session-a6616bd6-22de-4a22-8950-6315cc6931c2.json")
    # Una sesión local no es un recurso obligatorio de una instalación nueva.
    if not source.exists():
        pytest.skip("Sesión manual no distribuida.")
    before = source.read_bytes()
    session = load_session(source)
    assert [session["evaluations"][n - 1]["status"] for n in (4, 6)] == ["no_disponible", "no_disponible"]
    assert source.read_bytes() == before

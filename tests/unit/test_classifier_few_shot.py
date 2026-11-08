"""Demostraciones aprobadas y trazabilidad; no prueban acierto de un modelo."""

import json

import pytest

from harness.classifier_few_shot import CONFIG_PATH, load_few_shot, example_output
from harness.classification_references import load_classification_references
from harness.classification_evaluation import semantic_projection
from harness.llm_classification_contract import complete_llm_classification
from harness.llm_question_classifier import LLMQuestionClassifier
from tests.unit.test_llm_question_classifier import FakeClient, response, draft, classify


def test_selected_examples_are_approved_development_and_preserve_semantics():
    block, metadata = load_few_shot()
    suite = load_classification_references()
    cases = {c["case_id"]:c for c in suite.cases()}
    assert metadata["case_ids"] == ["R01", "R04", "R06", "R08", "R12", "R15"]
    for cid in metadata["case_ids"]:
        case = cases[cid]
        value = example_output(case)
        result = complete_llm_classification(value, expected_intervention_id=cid, expected_text=case["input"]["text"],
            allowed_context_turn_ids=tuple(c["turn_number"] for c in case["input"]["context_turns"]))
        assert semantic_projection(result) == semantic_projection(case["expected"])
        assert case["input"]["text"] in block
    assert metadata["reference_sha256"] == suite.source_sha256


@pytest.mark.parametrize("ids", [["R09"], ["R99"], ["R01", "R01"], []])
def test_reserved_unknown_or_duplicate_ids_are_rejected(ids, tmp_path):
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["case_ids"] = ids
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_few_shot(path)


def test_source_hash_mismatch_is_not_silently_accepted(tmp_path):
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["reference_sha256"] = "0"*64
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_few_shot(path)


def test_cache_does_not_expose_mutable_provenance():
    first, metadata = load_few_shot()
    metadata["case_ids"].clear()
    second, current = load_few_shot()
    assert first == second and len(current["case_ids"]) == 6


def test_disabled_mode_never_reads_demonstrations(monkeypatch):
    import harness.llm_question_classifier as module
    monkeypatch.setattr(module, "load_few_shot", lambda: pytest.fail("El control sin ejemplos no lee el corpus"))
    client = FakeClient(response(draft()))
    report = LLMQuestionClassifier(client, few_shot=False).classify("¿Qué es una función?", intervention_id="test-llm-001")
    assert not report.to_dict()["few_shot"]["enabled"]
    assert "DEMOSTRACIONES_FEW_SHOT" not in client.calls[0][0]["content"]


def test_runtime_uses_examples_but_current_turn_remains_separate_data():
    client = FakeClient(response(draft()))
    result = classify(client).to_dict()
    assert result["few_shot"]["enabled"] and len(result["few_shot"]["case_ids"]) == 6
    assert "DEMOSTRACIONES_FEW_SHOT_APROBADAS" in client.calls[0][0]["content"]
    assert json.loads(client.calls[0][1]["content"])["input"]["text"] == "¿Qué es una función?"
    result["few_shot"]["case_ids"].clear()
    assert len(classify(FakeClient(response(draft()))).to_dict()["few_shot"]["case_ids"]) == 6


def test_unapproved_reference_source_cannot_be_used(tmp_path):
    import hashlib
    suite = load_classification_references().to_dict()
    suite["approval"]["status"] = "pending"
    source = tmp_path / "references.json"
    source.write_text(json.dumps(suite), encoding="utf-8")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["reference_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_few_shot(path, source)


def test_evaluation_checkpoint_detects_changes_to_example_selection(tmp_path, monkeypatch):
    from scripts import evaluate_classifier
    for name in evaluate_classifier.FROZEN_SOURCES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"initial")
    monkeypatch.setattr(evaluate_classifier, "ROOT", tmp_path)
    before = evaluate_classifier.source_hashes()
    assert "harness/classifier_few_shot.py" in before
    (tmp_path / "config/classifier_few_shot.json").write_bytes(b"changed_selection")
    after = evaluate_classifier.source_hashes()
    assert before["config/classifier_few_shot.json"] != after["config/classifier_few_shot.json"]

"""Demostraciones aprobadas y separación entre entrenamiento, prueba e historial."""

from copy import deepcopy
import hashlib
import json

import pytest

from harness import question_evaluator
from harness.evaluation_contract import DEMONSTRATION_CASES, evaluation_generation_schema, validate_record
from harness.evaluator_few_shot import CONFIG_PATH, DEMONSTRATIONS_PATH, JOB_PATH, load_evaluator_examples
from harness.quality_references import REFERENCE_PATH
from harness.question_evaluator import QuestionEvaluator
from harness.scoring import load_rubric
from tests.evaluation_fixtures import EvaluationClient
from tests.unit.test_question_evaluation import evaluate, request


def copies(tmp_path):
    paths = []
    for number, source in enumerate((CONFIG_PATH, REFERENCE_PATH, DEMONSTRATIONS_PATH, JOB_PATH)):
        path = tmp_path / f"{number}.json"
        path.write_bytes(source.read_bytes())
        paths.append(path)
    return paths


def load(paths):
    return load_evaluator_examples(load_rubric(), *paths)


def test_six_approved_examples_have_literal_evidence_and_no_reserved_cases():
    block, metadata, _ = load_evaluator_examples(load_rubric())
    assert metadata["case_ids"] == list(DEMONSTRATION_CASES)
    assert all(identifier not in block for identifier in [f"E{n}" for n in range(31, 41)])
    assert "sin objetivo explícito de episodio" in block.lower()
    assert metadata["enabled"] and len(metadata["examples_sha256"]) == 64


def test_control_does_not_read_examples_or_references(monkeypatch):
    monkeypatch.setattr(question_evaluator, "load_evaluator_examples", lambda *args: pytest.fail("El control no lee demostraciones"))
    client = EvaluationClient()
    record = evaluate(QuestionEvaluator(client, few_shot=False))
    assert record["few_shot"]["reason"] == "disabled_by_option"
    assert "DEMOSTRACIONES APROBADAS" not in client.requests[0][0]["content"]


def test_actual_request_stays_outside_examples_and_metadata_is_independent():
    client = EvaluationClient()
    evaluator = QuestionEvaluator(client)
    data = request(evaluator, "¿Qué aprendiste de tu proyecto?")
    before = deepcopy(data)
    record = evaluate(evaluator, data)
    assert record["few_shot"]["enabled"] and record["evaluation_version"] == "1.3.0"
    assert json.loads(client.requests[0][1]["content"])["input"] == before == record["request"]
    assert not record["request"]["context_turns"]
    record["few_shot"]["case_ids"].clear()
    assert len(evaluate(evaluator)["few_shot"]["case_ids"]) == 6


def test_other_job_does_not_receive_incompatible_demonstrations():
    client = EvaluationClient()
    evaluator = QuestionEvaluator(client)
    data = request(evaluator)
    data["job"]["job_id"] = "otro-puesto"
    record = evaluate(evaluator, data)
    assert not record["few_shot"]["enabled"] and record["few_shot"]["reason"] == "job_incompatible"
    assert "DEMOSTRACIONES APROBADAS" not in client.requests[0][0]["content"]


@pytest.mark.parametrize("index", [1, 2, 3])
def test_changed_sources_are_not_injected(tmp_path, index):
    paths = copies(tmp_path)
    paths[index].write_bytes(paths[index].read_bytes() + b" ")
    with pytest.raises(ValueError, match="fuente"):
        load(paths)


@pytest.mark.parametrize("change", ["pending", "reserved", "levels", "reason"])
def test_recomputed_hashes_cannot_bypass_approval_or_expected_labels(tmp_path, change):
    paths = copies(tmp_path)
    config = json.loads(paths[0].read_text(encoding="utf-8"))
    ref = json.loads(paths[1].read_text(encoding="utf-8"))
    demo = json.loads(paths[2].read_text(encoding="utf-8"))
    case = next(c for c in ref["cases"] if c["case_id"] == "E03")
    if change == "pending":
        case.update(review_status="pending", reviewer=None)
    elif change == "reserved":
        case["split"] = "comprobacion_conocida"
    elif change == "levels":
        demo["examples"][0]["output"]["criteria"]["claridad"]["level"] = 2
    else:
        demo["examples"][0]["output"]["criteria"]["claridad"]["reason"] = "Justificación no aprobada."
    paths[1].write_text(json.dumps(ref), encoding="utf-8")
    paths[2].write_text(json.dumps(demo), encoding="utf-8")
    config["reference_sha256"] = hashlib.sha256(paths[1].read_bytes()).hexdigest()
    config["demonstrations_sha256"] = hashlib.sha256(paths[2].read_bytes()).hexdigest()
    paths[0].write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load(paths)


def test_new_record_requires_examples_audit_but_legacy_record_does_not():
    evaluator = QuestionEvaluator(EvaluationClient())
    record = evaluate(evaluator)
    del record["few_shot"]
    with pytest.raises(ValueError):
        validate_record(record, evaluator.rubric)
    record["evaluation_version"] = "1.2.0"
    validate_record(record, evaluator.rubric)


def test_alternative_weights_keep_examples_but_changed_descriptors_cannot_reuse_them():
    rubric = load_rubric()
    rubric["weights"] = dict(zip(("pertinencia", "enfoque", "claridad", "neutralidad"), (70, 10, 10, 10)))
    assert load_evaluator_examples(rubric)[1]["enabled"]
    rubric["descriptors"]["claridad"][0] = "Descriptor de otra rúbrica."
    with pytest.raises(ValueError, match="definición"):
        load_evaluator_examples(rubric)


def test_no_classification_cannot_generate_an_auxiliary_discrepancy():
    assert evaluation_generation_schema(classification_available=False)["properties"]["discrepancies"]["maxItems"] == 0
    assert evaluation_generation_schema(classification_available=True)["properties"]["discrepancies"]["maxItems"] == 4

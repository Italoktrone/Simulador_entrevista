"""No repetir principales; conservar interpretación, contradicciones y contrato público."""

from copy import deepcopy
import json

import pytest
from jsonschema import Draft202012Validator

from harness.classification_contract import ClassificationContractError, classification_expectation_schema
from harness.llm_classification_contract import (
    classification_generation_schema, classification_llm_schema, complete_llm_classification,
)
from tests.unit.test_llm_question_classifier import draft, classify, FakeClient, response


def complete(data):
    return complete_llm_classification(data, expected_intervention_id=data["intervention_id"],
        expected_text=data["original_text"])


@pytest.mark.parametrize("approaches,main,reason", [
    (["factual_tecnico"], "factual_tecnico", None),
    (["situacional"], "situacional", None),
    (["conductual", "situacional"], None, None),
    (["conductual", "situacional"], "conductual", "La petición prioriza el episodio relatado."),
])
def test_single_unit_copies_semantic_choice_including_absence_of_predominance(approaches, main, reason):
    value = draft()
    unit = value["units"][0]["classification"]
    unit.update(approaches=approaches, main_approach=main, main_approach_reason=reason)
    before = deepcopy(value)
    result = complete(value)
    assert value == before and value["classification"] == {}
    for key in ("main_approach", "main_approach_reason", "main_form", "main_form_reason", "rationale"):
        assert result["classification"][key] == result["units"][0]["classification"][key]
    assert result["contract_version"] == "1.0.0"


@pytest.mark.parametrize("field,value", [
    ("main_approach", "factual_tecnico"), ("main_approach_reason", "Razón duplicada"),
    ("main_form", "abierta"), ("main_form_reason", None), ("rationale", "Resumen duplicado"),
])
def test_redundant_global_fields_are_rejected_not_silently_overwritten(field, value):
    data = draft()
    data["classification"][field] = value
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "additionalProperties"
    assert not Draft202012Validator(classification_generation_schema(allowed_context_turn_ids=())).is_valid(data)


def test_single_unit_cannot_hide_a_wrong_reason_in_its_semantic_labels():
    data = draft()
    data["units"][0]["classification"]["main_approach_reason"] = "No existe una segunda etiqueta."
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "dominance_reason"
    assert caught.value.path == "/units/0/classification/main_approach_reason"


@pytest.mark.parametrize("version", ["1.1.0", "1.2.0"])
def test_old_wire_versions_cannot_be_mislabelled_as_new_generations(version):
    data = draft()
    data["contract_version"] = version
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_native_schema_distinguishes_zero_one_and_multiple_units():
    schema = classification_generation_schema(allowed_context_turn_ids=())
    Draft202012Validator.check_schema(schema)
    data = draft()
    assert Draft202012Validator(schema).is_valid(data)
    data["units"].append(deepcopy(data["units"][0]))
    assert not Draft202012Validator(schema).is_valid(data)
    # No se inventa una unidad o un principal para hacer pasar la salida.
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_generation_emits_units_before_committing_to_the_global_container():
    schema = classification_generation_schema(allowed_context_turn_ids=())
    for branch in schema["oneOf"]:
        keys = list(branch["properties"])
        assert keys.index("units") < keys.index("classification")
        assert branch["required"].index("units") < branch["required"].index("classification")


def test_short_generation_limit_does_not_truncate_or_change_public_rationales():
    public = classification_expectation_schema()["$defs"]["rationale"]["maxLength"]
    assert classification_llm_schema()["$defs"]["rationale"]["maxLength"] == public
    assert classification_generation_schema()["$defs"]["rationale"]["maxLength"] == 160
    data = draft()
    data["units"][0]["classification"]["rationale"] = "x" * public
    result = complete(data)
    assert result["classification"]["rationale"] == "x" * public


def test_overlong_rationale_has_specific_repair_without_replaying_or_truncating_text():
    value = draft()
    maximum = classification_expectation_schema()["$defs"]["rationale"]["maxLength"]
    text = "x" * (maximum + 1)
    value["units"][0]["classification"]["rationale"] = text
    client = FakeClient(response(value), response(draft()))
    report = classify(client)
    assert report.status == "clasificada" and len(report.attempts) == 2
    assert "160 caracteres" in client.calls[-1][0]["content"]
    assert text not in json.dumps(report.to_dict()) + client.calls[-1][0]["content"]

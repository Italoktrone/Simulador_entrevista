"""Anulación del principal global ajeno a las formas de unidades, sin elegir otro."""

from copy import deepcopy

import pytest

from harness.classification_contract import ClassificationContractError, validate_classification_expectation
from harness.llm_classification_contract import MISSING_GLOBAL_APPROACH_REASON, _normalize_global_main_form
from tests.unit.test_global_reason_completion import compound, complete
from tests.unit.test_llm_question_classifier import FakeClient, classify, draft, response


@pytest.mark.parametrize("main", ["opcion_multiple", "forma_inventada", "", None])
@pytest.mark.parametrize("reason", [None, "El modelo propone una prioridad incompatible."])
def test_nonmember_main_form_is_nulled_with_its_reason_without_mutating_input(main, reason):
    data = compound()
    data["classification"].update(main_form=main, main_form_reason=reason)
    before = deepcopy(data)
    result = complete(data)
    assert data == before
    assert result["classification"]["main_form"] is None
    assert result["classification"]["main_form_reason"] is None
    assert result["classification"]["forms"] == ["abierta", "cerrada"]
    assert [u["classification"]["forms"] for u in result["units"]] == [["cerrada"], ["abierta"]]
    assert [u["classification"]["main_form"] for u in result["units"]] == ["cerrada", "abierta"]


@pytest.mark.parametrize("main", ["abierta", "cerrada"])
def test_member_main_form_and_its_existing_reason_are_preserved(main):
    data = compound()
    data["classification"].update(main_form=main, main_form_reason="Prioridad explícita indicada por el modelo.")
    result = complete(data)
    assert result["classification"]["main_form"] == main
    assert result["classification"]["main_form_reason"] == data["classification"]["main_form_reason"]


def test_valid_unanimous_form_stays_primary_without_a_reason():
    data = compound()
    data["units"][1]["classification"].update(forms=["cerrada"], main_form="cerrada")
    data["classification"].update(main_form="cerrada", main_form_reason=None)
    result = complete(data)
    assert result["classification"]["forms"] == ["cerrada"]
    assert result["classification"]["main_form"] == "cerrada"
    assert result["classification"]["main_form_reason"] is None


def test_both_python_defenses_allow_a_synthetic_compound_without_extra_generation():
    data = compound()
    data["classification"].update(main_form="opcion_multiple", main_form_reason="Prioridad inválida.")
    client = FakeClient(response(data))
    report = classify(client, text=data["original_text"])
    assert report.status == "clasificada" and len(client.calls) == len(report.attempts) == 1
    assert report.result["technical_error"] is None
    assert report.result["classification"]["main_approach_reason"] == MISSING_GLOBAL_APPROACH_REASON
    assert report.result["classification"]["main_form"] is None
    assert len(report.result["units"]) == 2


def test_single_unit_does_not_accept_redundant_global_form():
    data = draft()
    data["classification"]["main_form"] = "opcion_multiple"
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "additionalProperties"


@pytest.mark.parametrize("main", [False, 0, [], {}])
def test_malformed_main_form_types_still_fail(main):
    data = compound()
    data["classification"]["main_form"] = main
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_valid_member_without_mandatory_reason_is_still_rejected():
    data = compound()
    data["classification"].update(main_form="cerrada", main_form_reason=None)
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "dominance_reason"
    assert caught.value.path == "/classification/main_form_reason"


def test_null_is_not_a_fabricated_primary_when_all_units_share_one_form():
    data = compound()
    data["units"][1]["classification"].update(forms=["cerrada"], main_form="cerrada")
    data["classification"].update(main_form="opcion_multiple", main_form_reason="Forma ajena.")
    normalized = _normalize_global_main_form(data)
    assert normalized["classification"]["main_form"] is None
    assert normalized["classification"]["main_form_reason"] is None
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "primary_membership"


@pytest.mark.parametrize("mutation", ["missing_main", "malformed_forms", "missing_forms"])
def test_incomplete_structure_is_not_silently_repaired(mutation):
    data = compound()
    data["classification"]["main_form"] = "opcion_multiple"
    if mutation == "missing_main":
        data["classification"].pop("main_form")
    elif mutation == "malformed_forms":
        data["units"][0]["classification"]["forms"] = [False]
    else:
        data["units"][0]["classification"].pop("forms")
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_public_validator_still_rejects_nonmember_main_form():
    result = complete(compound())
    result["classification"]["main_form"] = "opcion_multiple"
    with pytest.raises(ClassificationContractError) as caught:
        validate_classification_expectation(result, expected_intervention_id=result["intervention_id"],
                                             expected_text=result["original_text"])
    assert caught.value.rule == "primary_membership"

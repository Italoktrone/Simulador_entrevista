"""Razón por defecto autorizada, sin elegir predominio ni ocultar otros fallos."""

from copy import deepcopy

import pytest

from harness.classification_contract import ClassificationContractError, validate_classification_expectation
from harness.llm_classification_contract import MISSING_GLOBAL_APPROACH_REASON, complete_llm_classification
from tests.unit.test_llm_question_classifier import FakeClient, classify, draft, response


def compound():
    first, second = "¿Usaste Git?", "¿Qué harías si falla el servidor?"
    data = draft(first + " " + second, form="cerrada")
    data["units"][0]["quote"] = first
    other = draft(second, approach="situacional")["units"][0]
    other["unit_id"] = "u2"
    data["units"].append(other)
    data["classification"] = {
        "main_approach": "situacional", "main_approach_reason": None,
        "main_form": None, "main_form_reason": None,
        "rationale": "Dos peticiones independientes.",
    }
    return data


def complete(data):
    return complete_llm_classification(data, expected_intervention_id=data["intervention_id"],
                                       expected_text=data["original_text"])


@pytest.mark.parametrize("reason", [None, "", "missing"])
def test_missing_reason_is_completed_without_mutating_input_or_selecting_a_primary(reason):
    data = compound()
    if reason == "missing":
        data["classification"].pop("main_approach_reason")
    else:
        data["classification"]["main_approach_reason"] = reason
    before = deepcopy(data)
    result = complete(data)
    assert data == before
    assert result["classification"]["main_approach"] == "situacional"
    assert result["classification"]["main_approach_reason"] == MISSING_GLOBAL_APPROACH_REASON
    assert result["classification"]["secondary_approaches"] == ["factual_tecnico"]
    assert result["classification"]["main_form"] is None
    assert len(result["units"]) == 2
    assert [u["classification"]["main_approach_reason"] for u in result["units"]] == [None, None]


def test_existing_semantic_reason_is_preserved():
    data = compound()
    data["classification"]["main_approach_reason"] = "La actuación hipotética tiene prioridad explícita."
    result = complete(data)
    assert result["classification"]["main_approach_reason"] == data["classification"]["main_approach_reason"]


def test_no_predominance_does_not_receive_a_default_reason():
    data = compound()
    data["classification"]["main_approach"] = None
    result = complete(data)
    assert result["classification"]["main_approach"] is None
    assert result["classification"]["main_approach_reason"] is None
    assert result["classification"]["secondary_approaches"] == []


def test_only_one_approach_across_multiple_units_needs_no_reason():
    data = compound()
    data["units"][0]["classification"].update(approaches=["situacional"], main_approach="situacional")
    result = complete(data)
    assert result["classification"]["main_approach_reason"] is None
    assert result["classification"]["approaches"] == ["situacional"]


@pytest.mark.parametrize("reason", [False, 0, [], {}, "   "])
def test_invalid_reason_types_and_whitespace_still_fail(reason):
    data = compound()
    data["classification"]["main_approach_reason"] = reason
    with pytest.raises(ClassificationContractError):
        complete(data)


@pytest.mark.parametrize("mutation,rule", [
    ("form", "primary_membership"), ("no_primary_reason", "dominance_reason"),
    ("invalid_primary", "primary_membership"), ("quote", "quote_not_found"),
])
def test_other_defects_are_not_hidden_by_default_reason(mutation, rule):
    data = compound()
    if mutation == "form":
        data["units"][1]["classification"].update(forms=["cerrada"], main_form="cerrada")
    elif mutation == "no_primary_reason":
        data["classification"].update(main_approach=None, main_approach_reason="Explicación de empate.")
    elif mutation == "invalid_primary":
        data["classification"]["main_approach"] = "otro"
    else:
        data["units"][0]["quote"] = "Cita inventada."
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == rule


def test_single_unit_missing_semantic_reason_is_not_changed():
    data = draft()
    data["units"][0]["classification"].update(
        approaches=["situacional", "factual_tecnico"], main_approach="situacional", main_approach_reason=None)
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.path == "/units/0/classification/main_approach_reason"


def test_public_validator_remains_strict_and_does_not_invent_reasons():
    data = compound()
    result = complete(data)
    result["classification"]["main_approach_reason"] = None
    with pytest.raises(ClassificationContractError) as caught:
        validate_classification_expectation(result, expected_intervention_id=result["intervention_id"],
                                             expected_text=result["original_text"])
    assert caught.value.rule == "dominance_reason"


def test_classifier_accepts_missing_global_reason_without_an_extra_generation():
    data = compound()
    client = FakeClient(response(data))
    report = classify(client, text=data["original_text"])
    assert report.status == "clasificada"
    assert len(client.calls) == len(report.attempts) == 1
    assert report.result["technical_error"] is None
    assert report.result["classification"]["main_approach_reason"] == MISSING_GLOBAL_APPROACH_REASON


def test_classifier_still_rejects_missing_primary_for_unanimous_forms():
    data = compound()
    data["units"][1]["classification"].update(forms=["cerrada"], main_form="cerrada")
    client = FakeClient(response(data), response(data))
    report = classify(client, text=data["original_text"])
    assert report.status == "respaldo"
    assert report.result["technical_error"] == "contrato_invalido"
    assert len(client.calls) == 2
    assert all(a.validation_error.path == "/classification/main_form" for a in report.attempts)

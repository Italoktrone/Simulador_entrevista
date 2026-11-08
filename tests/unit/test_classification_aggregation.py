"""Derivación exacta y límites semánticos; sin llamadas ni ajuste de referencias."""

from copy import deepcopy
import pytest

from harness.classification_aggregation import GLOBAL_DERIVED_FIELDS
from harness.classification_contract import ClassificationContractError
from harness.classification_evaluation import semantic_projection, unit_comparison
from harness.classification_references import load_classification_references
from harness.llm_classification_contract import complete_llm_classification
from tests.wire_fixtures import to_wire


@pytest.fixture(scope="module")
def cases():
    return load_classification_references().to_dict()["cases"]


def wire(expected):
    data = to_wire(expected)
    for unit in data["units"]:
        unit["quote"] = unit.pop("text")
        unit.pop("source_start")
        unit.pop("source_end")
    return data


def complete(data):
    return complete_llm_classification(data, expected_intervention_id=data["intervention_id"],
        expected_text=data["original_text"], allowed_context_turn_ids=tuple(data["context_turn_ids"]))


@pytest.mark.parametrize("index", range(40))
def test_reconstructs_approved_annotations_without_changing_semantics_or_sources(cases, index):
    # Reconstrucción determinista desde etiquetas humanas, NO evaluación LLM.
    expected = cases[index]["expected"]
    data = wire(expected)
    before = deepcopy(data)
    result = complete(data)
    assert data == before
    assert result["contract_version"] == "1.0.0"
    assert semantic_projection(result) == semantic_projection(expected)


@pytest.mark.parametrize("field", GLOBAL_DERIVED_FIELDS)
def test_global_derived_fields_from_model_are_rejected_instead_of_overwritten(cases, field):
    data = wire(cases[0]["expected"])
    data["classification"][field] = cases[0]["expected"]["classification"][field]
    with pytest.raises(ClassificationContractError) as error:
        complete(data)
    assert error.value.rule == "additionalProperties"


def test_unit_secondaries_are_also_forbidden_in_wire_input(cases):
    data = wire(cases[0]["expected"])
    data["units"][0]["classification"]["secondary_approaches"] = []
    with pytest.raises(ClassificationContractError) as error:
        complete(data)
    assert error.value.rule == "additionalProperties"


def test_canonical_order_secondaries_and_semantic_predominance_are_preserved(cases):
    data = wire(cases[0]["expected"])
    labels = data["units"][0]["classification"]
    labels.update(approaches=["factual_tecnico", "situacional", "conductual"],
                  main_approach="situacional", main_approach_reason="Predominio supuesto por el modelo.",
                  attributes=["sugestiva", "directiva"])
    result = complete(data)
    for actual in (result["classification"], result["units"][0]["classification"]):
        assert actual["approaches"] == ["conductual", "situacional", "factual_tecnico"]
        assert actual["attributes"] == ["directiva", "sugestiva"]
        assert actual["secondary_approaches"] == ["conductual", "factual_tecnico"]
        assert actual["main_approach"] == "situacional"
    labels.update(main_approach=None, main_approach_reason=None)
    result = complete(data)
    assert result["classification"]["main_approach"] is None
    assert result["classification"]["secondary_approaches"] == []
    assert result["units"][0]["classification"]["secondary_approaches"] == []


@pytest.mark.parametrize(("certainty", "expected"), [("clara", "clara"), ("ambigua", "ambigua"),
    ("indeterminada", "ambigua")])
def test_global_certainty_and_unknown_union_use_existing_rules(cases, certainty, expected):
    data = wire(cases[0]["expected"])
    first = data["units"][0]
    second = deepcopy(first)
    data["original_text"] = first["quote"] + " Segunda petición."
    second.update(unit_id="u2", quote="Segunda petición.")
    second["classification"]["certainty"] = certainty
    if certainty == "indeterminada":
        second["classification"].update(approaches=["indeterminado"], main_approach="indeterminado",
            forms=["indeterminada"], main_form="indeterminada")
    data["units"].append(second)
    data["classification"] = {k: first["classification"][k] for k in (
        "main_approach", "main_approach_reason", "main_form", "main_form_reason", "rationale")}
    result = complete(data)
    assert result["classification"]["certainty"] == expected
    assert result["classification"]["approaches"] == first["classification"]["approaches"]
    assert result["classification"]["forms"] == first["classification"]["forms"]


def test_all_unknown_remains_unknown(cases):
    data = wire(cases[0]["expected"])
    labels = data["units"][0]["classification"]
    labels.update(approaches=["indeterminado"], main_approach="indeterminado", forms=["indeterminada"],
                  main_form="indeterminada", certainty="indeterminada")
    result = complete(data)
    assert result["classification"]["certainty"] == "indeterminada"
    assert result["classification"]["secondary_approaches"] == []


def test_incompatible_global_principal_is_rejected_not_reselected(cases):
    data = wire(cases[0]["expected"])
    data["classification"]["main_approach"] = "indeterminado"
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_omitted_request_can_pass_contract_but_fails_segmentation_reference(cases):
    expected = next(c["expected"] for c in cases if len(c["expected"]["units"]) > 1)
    data = wire(expected)
    data["units"] = data["units"][:1]
    data["classification"] = {}
    result = complete(data)
    assert unit_comparison(expected, result) == {"segmentation_exact": False, "unit_labels_exact": None}


def test_old_wire_version_is_rejected_in_new_generation(cases):
    data = wire(cases[0]["expected"])
    data["contract_version"] = "1.1.0"
    with pytest.raises(ClassificationContractError):
        complete(data)

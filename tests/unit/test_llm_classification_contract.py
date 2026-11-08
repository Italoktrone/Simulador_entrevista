"""Citas literales, ambigüedad, compatibilidad y vocabulario del modelo 1.2."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from harness.classification_contract import ClassificationContractError
from harness.llm_classification_contract import (
    classification_llm_schema, classification_generation_schema, complete_llm_classification, locate_quotes,
)


TEXT = "El servidor acaba de fallar durante una entrega. Explica cómo actuarías."


def labels(approach="situacional", form="abierta"):
    return {"approaches": [approach], "main_approach": approach, 
            "main_approach_reason": None, "forms": [form], "main_form": form, "main_form_reason": None,
            "attributes": [], "certainty": "clara", "rationale": "Anotación sintética para verificar contratos."}


def wire(original=TEXT, quotes=None):
    quotes = [original] if quotes is None else quotes
    return to_wire({'contract_version': '1.1.0', 'intervention_id': 'quotes-test', 'original_text': original, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels(), 'units': [{'unit_id': f'u{i}', 'quote': q, 'classification': labels(), 'context_status': 'no_necesario', 'followup_of': None, 'depends_on': None} for i, q in enumerate(quotes, 1)], 'context_turn_ids': [], 'rationale': 'Entrada sintética; no mide un modelo real.'})


def complete(data):
    return complete_llm_classification(data, expected_intervention_id="quotes-test", expected_text=data["original_text"])


def test_quote_restores_real_offsets_and_public_contract_without_mutating_model_output():
    data = wire()
    before = deepcopy(data)
    result = complete(data)
    assert data == before
    assert result["contract_version"] == "1.0.0"
    assert result["units"][0]["text"] == TEXT
    assert result["units"][0]["source_start"] == 0
    assert result["units"][0]["source_end"] == 72
    assert "quote" not in result["units"][0]
    assert "source_end" not in data["units"][0]


@pytest.mark.parametrize(("original", "quotes", "expected"), [
    ("👋 café y té.", ["café", "té."], [(2, 6), (9, 12)]),
    ("\r\n sí\t", [" sí\t"], [(2, 6)]),
    ("Sí. Sí.", ["Sí.", "Sí."], [(0, 3), (4, 7)]),
    ("A B A", ["A", "B"], [(0, 1), (2, 3)]),
    ("", [], []),
])
def test_find_uses_codepoints_and_joint_order_to_locate_unambiguous_fragments(original, quotes, expected):
    assert locate_quotes(original, quotes) == expected


@pytest.mark.parametrize(("original", "quotes", "rule"), [
    ("Sí. Sí.", ["Sí."], "quote_ambiguous"),
    ("Sí. Sí. Sí.", ["Sí.", "Sí."], "quote_ambiguous"),
    ("A B", ["B", "A"], "quote_order"),
    ("ababa", ["aba", "aba"], "quote_order"),
    ("Café", ["Cafe"], "quote_not_found"),
    ("café", ["cafe\u0301"], "quote_not_found"),
    ("A B", ["A  B"], "quote_not_found"),
    ("texto", [""], "quote_input"),
    ("texto", ["  "], "quote_input"),
])
def test_missing_ambiguous_reordered_or_overlapping_quotes_are_rejected(original, quotes, rule):
    with pytest.raises(ClassificationContractError) as caught:
        locate_quotes(original, quotes)
    assert caught.value.rule == rule


@pytest.mark.parametrize("field", ["source_start", "source_end", "text"])
def test_model_indices_and_old_unit_text_field_are_forbidden(field):
    data = wire()
    data["units"][0][field] = 0 if field != "text" else TEXT
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "additionalProperties"


def test_missing_literal_quote_is_a_contract_error_not_a_fabricated_span():
    data = wire()
    data["units"][0]["quote"] = "Una frase que nunca apareció."
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "quote_not_found"


def test_model_cannot_replace_trusted_original_to_make_a_quote_match():
    data = wire("Otra fuente.")
    with pytest.raises(ClassificationContractError) as caught:
        complete_llm_classification(data, expected_intervention_id="quotes-test", expected_text=TEXT)
    assert caught.value.rule == "source_identity"


@pytest.mark.parametrize(("field", "value"), [
    ("approaches", ["ilegal"]), ("forms", ["directiva"]), ("attributes", ["coercitiva"]),
    ("forms", ["abierta", "abierta"]), ("attributes", ["directiva", "directiva"]),
])
def test_label_enums_and_uniqueness_are_still_validated_locally(field, value):
    data = wire()
    data["units"][0]["classification"][field] = value
    with pytest.raises(ClassificationContractError):
        complete(data)


def test_generation_choices_are_unique_canonical_sets_of_existing_labels():
    schema = classification_generation_schema()
    for name in ("unit_classification",):
        props = schema["$defs"][name]["properties"]
        for field in ("approaches", "forms", "attributes"):
            item = props[field]
            assert item["uniqueItems"] is True
            for option in item["enum"]:
                assert len(option) == len(set(option))
                domain = (schema["$defs"]["known_approach"]["enum"] if field == "secondary_approaches" else
                          schema["$defs"]["approach"]["enum"] if field == "approaches" else
                          schema["$defs"]["form"]["enum"] if field == "forms" else item["items"]["enum"])
                assert set(option) <= set(domain)
            if name == "unit_classification" and field == "forms":
                assert all(len(option) == 1 for option in item["enum"])


def test_parser_accepts_label_permutations_while_generation_uses_canonical_presentation():
    first, second = "¿Usaste Git?", "¿Cómo actuarías?"
    data = wire(first + " " + second, [first, second])
    data["units"][0]["classification"] = labels("factual_tecnico", "cerrada")
    data["classification"].update(main_approach=None, main_form=None)
    data["units"][0]["classification"].update(approaches=["factual_tecnico", "situacional"], main_approach_reason="Prioridad técnica explícita")
    result = complete(data)
    assert result["classification"]["main_approach"] is None
    assert result["units"][1]["source_start"] == len(first) + 1
    assert not Draft202012Validator(classification_generation_schema()).is_valid(data)


def test_other_relational_rules_are_not_relaxed_after_finding_offsets():
    data = wire()
    data["units"][0]["classification"]["main_approach_reason"] = "Explicación general mal ubicada."
    with pytest.raises(ClassificationContractError) as caught:
        complete(data)
    assert caught.value.rule == "dominance_reason"


def test_nonevaluable_protocol_needs_no_quotes_and_keeps_public_shape():
    data = wire("Hola", [])
    data.update(evaluability="no_evaluable", non_evaluable_reason="saludo", classification=None)
    result = complete(data)
    assert result["units"] == [] and result["classification"] is None
    assert result["contract_version"] == "1.0.0"


def test_exported_model_schema_matches_runtime_and_snapshots_are_independent():
    path = Path(__file__).resolve().parents[2] / "schemas/llm_question_classification.schema.json"
    assert json.loads(path.read_text(encoding="utf-8")) == classification_llm_schema()
    schema = classification_llm_schema()
    schema["$defs"]["unit"]["properties"].clear()
    assert "quote" in classification_llm_schema()["$defs"]["unit"]["properties"]


@pytest.mark.parametrize("ids", [(), (1,), (2, 3), (3, 6, 9)])
def test_request_schema_closes_context_and_followup_domains(ids):
    schema = classification_generation_schema(allowed_context_turn_ids=ids)
    Draft202012Validator.check_schema(schema)
    turns = Draft202012Validator({"$defs": schema["$defs"], "$ref":"#/$defs/turn_ids"})
    followup = Draft202012Validator(schema["$defs"]["unit"]["properties"]["followup_of"])
    assert turns.is_valid([]) and followup.is_valid(None)
    assert turns.is_valid(list(ids))
    for number in range(0, 11):
        assert turns.is_valid([number]) == (number in ids)
        assert followup.is_valid(number) == (number in ids)
    if ids:
        assert not turns.is_valid([ids[0], ids[0]])


@pytest.mark.parametrize("ids", [[1], (True,), (0,), (2, 1), (1, 1)])
def test_request_schema_rejects_invalid_trusted_turn_numbers(ids):
    with pytest.raises(ValueError):
        classification_generation_schema(allowed_context_turn_ids=ids)


def test_per_request_constraints_do_not_leak_into_other_schema_snapshots():
    original = classification_generation_schema()
    first = classification_generation_schema(allowed_context_turn_ids=(2, 3))
    first["$defs"]["turn_ids"]["items"]["enum"].append(99)
    empty = classification_generation_schema(allowed_context_turn_ids=())
    assert empty["$defs"]["turn_ids"]["enum"] == [[]]
    assert empty["$defs"]["unit"]["properties"]["followup_of"]["enum"] == [None]
    assert classification_generation_schema() == original


@pytest.mark.parametrize("definition", ["unit_classification"])
@pytest.mark.parametrize("approaches,main,reason,valid", [
    (["factual_tecnico"],"factual_tecnico",None,True),
    (["factual_tecnico"],"factual_tecnico","Razón improcedente",False),
    (["situacional","factual_tecnico"],None,None,True),
    (["situacional","factual_tecnico"],None,"Razón improcedente",False),
    (["situacional","factual_tecnico"],"situacional",None,False),
    (["situacional","factual_tecnico"],"situacional","Prioridad explícita",True),
])
def test_native_priority_choices_enforce_null_and_nonempty_reason(definition,approaches,main,reason,valid):
    schema = classification_generation_schema(allowed_context_turn_ids=())
    Draft202012Validator.check_schema(schema)
    value = labels("factual_tecnico","abierta")
    value.update(approaches=approaches,main_approach=main,main_approach_reason=reason)
    validator = Draft202012Validator({"$defs":schema["$defs"],"$ref":f"#/$defs/{definition}"})
    assert validator.is_valid(value) == valid


@pytest.mark.parametrize("definition", ["unit_classification"])
def test_native_approach_grammar_accepts_all_valid_priorities_and_rejects_bad_secondaries(definition):
    generic = classification_generation_schema()
    sets = generic["$defs"][definition]["properties"]["approaches"]["enum"]
    schema = classification_generation_schema(allowed_context_turn_ids=())
    validator = Draft202012Validator({"$defs":schema["$defs"],"$ref":f"#/$defs/{definition}"})
    for present in sets:
        for main in present if len(present) == 1 else [None,*present]:
            value = labels("factual_tecnico","abierta")
            secondary = [v for v in present if v != main and v != "indeterminado"] if main is not None else []
            value.update(approaches=present,main_approach=main,
                         main_approach_reason="Prioridad justificada" if len(present)>1 and main is not None else None)
            assert validator.is_valid(value), (present,main)
            value["secondary_approaches"] = ["otro"] if secondary != ["otro"] else []
            assert not validator.is_valid(value), (present,main)

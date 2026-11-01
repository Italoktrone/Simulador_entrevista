"""Pruebas del contrato público del validador estructural compartido."""

import copy
import json
from pathlib import Path

import pytest

from harness.schema_validator import (
    DataValidationError,
    InvalidSchemaError,
    validate_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = {
    "candidate": (
        "data/candidates/candidato_junior.json",
        "schemas/candidate.schema.json",
        "candidate_id",
    ),
    "job": (
        "data/jobs/desarrollador_junior.json",
        "schemas/job.schema.json",
        "job_id",
    ),
}


@pytest.fixture(params=["candidate", "job"])
def document_pair(request):
    data_name, schema_name, identifier = DOCUMENTS[request.param]
    data_path = PROJECT_ROOT / data_name
    schema_path = PROJECT_ROOT / schema_name
    return {
        "data": json.loads(data_path.read_text(encoding="utf-8")),
        "schema": json.loads(schema_path.read_text(encoding="utf-8")),
        "identifier": identifier,
        "paths": (data_path, schema_path),
    }


def load_candidate():
    data_name, schema_name, _ = DOCUMENTS["candidate"]
    data = json.loads((PROJECT_ROOT / data_name).read_text(encoding="utf-8"))
    schema = json.loads((PROJECT_ROOT / schema_name).read_text(encoding="utf-8"))
    return data, schema


def test_accepts_approved_data_without_mutating_inputs(document_pair):
    data, schema = document_pair["data"], document_pair["schema"]
    original_data, original_schema = copy.deepcopy(data), copy.deepcopy(schema)

    assert validate_data(data, schema) is None

    assert data == original_data
    assert schema == original_schema


def test_reports_missing_identifier_without_mutating_inputs(document_pair):
    data, schema = document_pair["data"], document_pair["schema"]
    identifier = document_pair["identifier"]
    del data[identifier]
    original_data, original_schema = copy.deepcopy(data), copy.deepcopy(schema)

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "raíz"
    assert caught.value.rule == "required"
    assert identifier in str(caught.value)
    assert data == original_data
    assert schema == original_schema


def test_validation_keeps_source_files_unchanged(document_pair):
    paths = document_pair["paths"]
    before = [path.read_bytes() for path in paths]

    validate_data(document_pair["data"], document_pair["schema"])

    assert [path.read_bytes() for path in paths] == before


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "inexistente"},
        {"type": "object", "required": "name"},
        {"type": "object", "properties": {"name": {"minLength": -1}}},
    ],
    ids=["unknown-type", "required-not-list", "negative-minimum-length"],
)
def test_distinguishes_invalid_schema_from_invalid_data(schema):
    with pytest.raises(InvalidSchemaError, match="El esquema"):
        validate_data({}, schema)


@pytest.mark.parametrize("data", [None, [], "texto", True])
def test_reports_wrong_root_type(data):
    with pytest.raises(DataValidationError) as caught:
        validate_data(data, {"type": "object"})

    assert caught.value.path == "raíz"
    assert caught.value.rule == "type"


def test_reports_nested_field_and_list_index():
    data, schema = load_candidate()
    data["education"][0]["start_month"] = "2022-13"

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "/education/0/start_month"
    assert caught.value.rule == "pattern"


def test_names_missing_field_inside_nested_object():
    data, schema = load_candidate()
    del data["education"][0]["institution"]

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "/education/0"
    assert "institution" in str(caught.value)


def test_rejects_duplicate_list_items():
    data, schema = load_candidate()
    data["tools_used"] = ["VS Code", "VS Code"]

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "/tools_used"
    assert caught.value.rule == "uniqueItems"


def test_reports_project_alternative_without_dumping_its_contents():
    data, schema = load_candidate()
    project_name = data["projects"][0]["name"]
    del data["projects"][0]["role_id"]

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "/projects/0"
    assert caught.value.rule == "oneOf"
    assert project_name not in str(caught.value)


def test_error_message_omits_rejected_value():
    data, schema = load_candidate()
    rejected_value = "VALOR_PRIVADO_DE_PRUEBA"
    data["candidate_id"] = rejected_value

    with pytest.raises(DataValidationError) as caught:
        validate_data(data, schema)

    assert caught.value.path == "/candidate_id"
    assert rejected_value not in str(caught.value)
    assert data["name"] not in str(caught.value)


def test_does_not_fill_missing_values_from_schema_defaults():
    data = {}
    schema = {"type": "object", "properties": {"name": {"default": "No agregar"}}}

    validate_data(data, schema)

    assert data == {}


def test_escapes_special_characters_in_error_path():
    schema = {
        "type": "object",
        "properties": {
            "a/b": {"type": "object", "properties": {"x~y": {"type": "string"}}}
        },
    }

    with pytest.raises(DataValidationError) as caught:
        validate_data({"a/b": {"x~y": 7}}, schema)

    assert caught.value.path == "/a~1b/x~0y"


@pytest.mark.parametrize("case", ["nonexistent-reference", "impossible-date"])
def test_semantic_checks_remain_outside_structural_validator(case):
    data, schema = load_candidate()
    if case == "nonexistent-reference":
        data["professional_competencies"][0]["situation_ids"] = ["S9999"]
    else:
        data["scenario_reference_date"] = "2026-02-31"

    assert validate_data(data, schema) is None

"""Lectura y validación de los documentos aprobados, sin consultar un LLM."""

import hashlib
from pathlib import Path

import pytest

from harness.json_loader import load_json
from harness.schema_validator import validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("data_name", "schema_name", "expected_hash"),
    [
        (
            "data/candidates/candidato_junior.json",
            "schemas/candidate.schema.json",
            "6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3",
        ),
        (
            "data/jobs/desarrollador_junior.json",
            "schemas/job.schema.json",
            "40C16AEEB4D41BE7FC0EFF3D8237178C883CAD294E9D04F96C4D4F9B81455F77",
        ),
    ],
    ids=["approved-candidate", "approved-job"],
)
def test_loads_and_validates_approved_documents_without_changes(
    data_name, schema_name, expected_hash
):
    data_path = PROJECT_ROOT / data_name
    schema_path = PROJECT_ROOT / schema_name
    before_data = data_path.read_bytes()
    before_schema = schema_path.read_bytes()
    assert hashlib.sha256(before_data).hexdigest().upper() == expected_hash

    data = load_json(data_path)
    schema = load_json(schema_path)
    validate_data(data, schema)

    assert data_path.read_bytes() == before_data
    assert schema_path.read_bytes() == before_schema

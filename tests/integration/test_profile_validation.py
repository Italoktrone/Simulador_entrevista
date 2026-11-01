"""Lectura y validación de coherencia del perfil real aprobado."""

import hashlib
from pathlib import Path

from harness.application.cli import format_resume
from harness.json_loader import load_json
from harness.profile import load_profile, validate_profile_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_approved_profile_passes_both_layers_without_file_changes():
    profile_path = PROJECT_ROOT / "data/candidates/candidato_junior.json"
    schema_path = PROJECT_ROOT / "schemas/candidate.schema.json"
    original = profile_path.read_bytes()
    original_schema = schema_path.read_bytes()

    validate_profile_data(load_json(profile_path), load_json(schema_path))

    assert profile_path.read_bytes() == original
    assert schema_path.read_bytes() == original_schema
    assert hashlib.sha256(original).hexdigest().upper() == (
        "6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3"
    )


def test_loads_protected_approved_profile_and_checks_integrity():
    profile_path = PROJECT_ROOT / "data/candidates/candidato_junior.json"
    before = profile_path.read_bytes()

    profile = load_profile(profile_path)
    exported = profile.to_dict()
    exported["name"] = "Cambio solo en una copia de prueba"

    assert profile.candidate_id == "cand-001"
    assert profile.scenario_reference_date == "2026-10-20"
    assert profile.to_dict()["name"] == "Nicolás Vera Soto"
    assert profile.source_sha256 == (
        "6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3"
    )
    assert profile.assert_source_unchanged() is None
    assert profile_path.read_bytes() == before


def test_derives_and_formats_public_resume_without_changing_approved_profile():
    profile_path = PROJECT_ROOT / "data/candidates/candidato_junior.json"
    before = profile_path.read_bytes()
    profile = load_profile(profile_path)

    text = format_resume(profile)

    assert "Nicolás Vera Soto" in text
    assert "Soluciones Digitales Faro" in text
    assert "MesaFaro" in text
    assert "Inventario Aula" in text
    assert "INNER JOIN" not in text
    assert "necesitó cuatro" not in text
    assert "necesita apoyo para diseñar estrategias" not in text
    assert profile.assert_source_unchanged() is None
    assert profile_path.read_bytes() == before

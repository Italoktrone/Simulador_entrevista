"""Protección de la instantánea e integridad de copias temporales del perfil."""

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import harness.profile as profile_module
from harness.json_loader import JsonLoadError, load_json
from harness.profile import (
    ProfileConsistencyError,
    ProfileIntegrityError,
    load_profile,
)
from harness.schema_validator import DataValidationError, InvalidSchemaError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def source_copy(tmp_path):
    source = PROJECT_ROOT / "data/candidates/candidato_junior.json"
    path = tmp_path / "candidato.json"
    path.write_bytes(source.read_bytes())
    return path


def test_loads_validated_profile_with_original_hash(source_copy):
    before = source_copy.read_bytes()

    profile = load_profile(source_copy)

    assert profile.candidate_id == "cand-001"
    assert profile.scenario_reference_date == "2026-10-20"
    assert profile.source_path == source_copy.resolve()
    assert profile.source_sha256 == hashlib.sha256(before).hexdigest().upper()
    assert profile.to_dict() == load_json(source_copy)
    assert source_copy.read_bytes() == before


@pytest.mark.parametrize("attribute", ["source_path", "source_sha256", "_snapshot_json"])
def test_snapshot_fields_cannot_be_reassigned(source_copy, attribute):
    profile = load_profile(source_copy)

    with pytest.raises(FrozenInstanceError):
        setattr(profile, attribute, "cambio")

    assert profile.candidate_id == "cand-001"


def test_exported_copies_cannot_modify_snapshot_or_source(source_copy):
    before = source_copy.read_bytes()
    profile = load_profile(source_copy)
    expected = profile.to_dict()

    exported = profile.to_dict()
    exported["candidate_id"] = "cand-999"
    exported["projects"][0]["name"] = "Cambio en una copia"
    exported["tools_used"].append("Otra herramienta")

    assert profile.to_dict() == expected
    assert source_copy.read_bytes() == before


def test_repr_does_not_dump_internal_profile(source_copy):
    profile = load_profile(source_copy)

    assert "Nicolás" not in repr(profile)
    assert "MesaFaro" not in repr(profile)
    assert "_snapshot_json" not in repr(profile)


def test_integrity_check_accepts_unchanged_source(source_copy):
    profile = load_profile(source_copy)

    assert profile.assert_source_unchanged() is None


@pytest.mark.parametrize("change", ["formatting", "facts"])
def test_detects_source_changes_and_keeps_snapshot(source_copy, change):
    profile = load_profile(source_copy)
    expected = profile.to_dict()
    if change == "formatting":
        source_copy.write_bytes(source_copy.read_bytes() + b"\n")
    else:
        changed = profile.to_dict()
        changed["name"] = "Otra persona de prueba"
        source_copy.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(ProfileIntegrityError) as caught:
        profile.assert_source_unchanged()

    assert caught.value.rule == "source_changed"
    assert caught.value.path == source_copy.resolve()
    assert profile.to_dict() == expected


def test_reports_deleted_source(source_copy):
    profile = load_profile(source_copy)
    source_copy.unlink()

    with pytest.raises(ProfileIntegrityError) as caught:
        profile.assert_source_unchanged()

    assert caught.value.rule == "source_missing"


def test_reports_unreadable_source(source_copy, monkeypatch):
    profile = load_profile(source_copy)

    def deny_read(self):
        raise PermissionError("Permiso denegado de prueba")

    monkeypatch.setattr(Path, "read_bytes", deny_read)

    with pytest.raises(ProfileIntegrityError) as caught:
        profile.assert_source_unchanged()

    assert caught.value.rule == "source_unreadable"


def test_relative_source_stays_bound_after_working_directory_change(source_copy, tmp_path, monkeypatch):
    monkeypatch.chdir(source_copy.parent)
    profile = load_profile(source_copy.name)
    other_directory = tmp_path / "otra-carpeta"
    other_directory.mkdir()

    monkeypatch.chdir(other_directory)

    assert profile.assert_source_unchanged() is None
    assert profile.source_path == source_copy


def test_rejects_structurally_invalid_source(source_copy):
    source_copy.write_text('{"candidate_id":"cand-001"}', encoding="utf-8")

    with pytest.raises(DataValidationError):
        load_profile(source_copy)


def test_rejects_incoherent_source(source_copy):
    data = load_json(source_copy)
    data["scenario_reference_date"] = "2026-02-31"
    source_copy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ProfileConsistencyError):
        load_profile(source_copy)


def test_accepts_explicit_schema_path(source_copy, tmp_path):
    schema_path = tmp_path / "esquema.json"
    schema_path.write_bytes((PROJECT_ROOT / "schemas/candidate.schema.json").read_bytes())

    assert load_profile(source_copy, schema_path).candidate_id == "cand-001"


def test_rejects_invalid_schema(source_copy, tmp_path):
    schema_path = tmp_path / "esquema-invalido.json"
    schema_path.write_text('{"type":"inexistente"}', encoding="utf-8")

    with pytest.raises(InvalidSchemaError):
        load_profile(source_copy, schema_path)


def test_detects_source_change_during_validation(source_copy, monkeypatch):
    original_validate = profile_module.validate_profile_data

    def validate_then_change(data, schema):
        original_validate(data, schema)
        source_copy.write_bytes(source_copy.read_bytes() + b"\n")

    monkeypatch.setattr(profile_module, "validate_profile_data", validate_then_change)

    with pytest.raises(ProfileIntegrityError) as caught:
        load_profile(source_copy)

    assert caught.value.rule == "source_changed"


def test_reports_missing_source_before_snapshot_creation(tmp_path):
    with pytest.raises(JsonLoadError):
        load_profile(tmp_path / "ausente.json")

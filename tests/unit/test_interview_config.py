"""Carga conjunta, correspondencia de identificadores e independencia."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import harness.interview_config as config_module
from harness.interview_config import InterviewConfigError, load_interview_setup
from harness.json_loader import JsonLoadError, load_json
from harness.profile import ProfileConsistencyError, ProfileIntegrityError
from harness.schema_validator import DataValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def documents(tmp_path):
    sources = {
        "config": "config/interviews/basica.json",
        "candidate": "data/candidates/candidato_junior.json",
        "job": "data/jobs/desarrollador_junior.json",
    }
    paths = {}
    for name, source in sources.items():
        paths[name] = tmp_path / f"{name}.json"
        paths[name].write_bytes((PROJECT_ROOT / source).read_bytes())
    return paths


def load_documents(paths):
    return load_interview_setup(paths["config"], paths["candidate"], paths["job"])


def test_loads_matching_documents_without_changing_files(documents):
    before = {name: path.read_bytes() for name, path in documents.items()}

    setup = load_documents(documents)

    assert setup.candidate.candidate_id == "cand-001"
    assert setup.config_dict()["candidate_id"] == setup.candidate.candidate_id
    assert setup.config_dict()["job_id"] == setup.job_dict()["job_id"]
    assert setup.candidate.to_dict()["target_job_id"] == setup.job_dict()["job_id"]
    assert setup.job_dict()["title"] == "Desarrollador de Software Junior"
    assert setup.config_dict()["max_questions"] == 20
    assert {name: path.read_bytes() for name, path in documents.items()} == before


@pytest.mark.parametrize(
    ("document", "field", "value", "path", "rule"),
    [
        ("config", "candidate_id", "cand-999", "/configuration/candidate_id", "candidate_mismatch"),
        ("candidate", "candidate_id", "cand-002", "/configuration/candidate_id", "candidate_mismatch"),
        ("config", "job_id", "puesto-otro-999", "/configuration/job_id", "job_mismatch"),
        ("job", "job_id", "puesto-otro-999", "/configuration/job_id", "job_mismatch"),
        ("candidate", "target_job_id", "puesto-otro-999", "/candidate/target_job_id", "target_job_mismatch"),
    ],
)
def test_rejects_mismatched_references(documents, document, field, value, path, rule):
    data = load_json(documents[document])
    data[field] = value
    write_json(documents[document], data)
    before = {name: file.read_bytes() for name, file in documents.items()}

    with pytest.raises(InterviewConfigError) as caught:
        load_documents(documents)

    assert caught.value.path == path
    assert caught.value.rule == rule
    assert {name: file.read_bytes() for name, file in documents.items()} == before


def test_accepts_other_consistent_ids_without_hardcoding_initial_values(documents):
    config = load_json(documents["config"])
    config.update(candidate_id="cand-002", job_id="puesto-otro-002")
    candidate = load_json(documents["candidate"])
    candidate.update(candidate_id="cand-002", target_job_id="puesto-otro-002")
    job = load_json(documents["job"])
    job["job_id"] = "puesto-otro-002"
    for name, data in (("config", config), ("candidate", candidate), ("job", job)):
        write_json(documents[name], data)

    setup = load_documents(documents)

    assert setup.candidate.candidate_id == "cand-002"
    assert setup.job_dict()["job_id"] == "puesto-otro-002"


def test_validates_config_before_loading_other_documents(documents):
    config = load_json(documents["config"])
    config["max_questions"] = 21
    write_json(documents["config"], config)
    documents["candidate"].unlink()

    with pytest.raises(DataValidationError) as caught:
        load_documents(documents)

    assert caught.value.path == "/max_questions"


def test_validates_job_schema(documents):
    job = load_json(documents["job"])
    del job["requirements"]
    write_json(documents["job"], job)

    with pytest.raises(DataValidationError) as caught:
        load_documents(documents)

    assert caught.value.rule == "required"
    assert "requirements" in str(caught.value)


def test_validates_candidate_coherence(documents):
    candidate = load_json(documents["candidate"])
    candidate["scenario_reference_date"] = "2026-02-31"
    write_json(documents["candidate"], candidate)

    with pytest.raises(ProfileConsistencyError):
        load_documents(documents)


@pytest.mark.parametrize("name", ["config", "candidate", "job"])
def test_reports_missing_document(documents, name):
    documents[name].unlink()

    with pytest.raises(JsonLoadError) as caught:
        load_documents(documents)

    assert caught.value.path == documents[name]


def test_reports_invalid_job_json(documents):
    documents["job"].write_text("{", encoding="utf-8")

    with pytest.raises(JsonLoadError):
        load_documents(documents)


def test_config_and_job_exports_are_independent_copies(documents):
    setup = load_documents(documents)
    expected_config, expected_job = setup.config_dict(), setup.job_dict()

    config_copy = setup.config_dict()
    config_copy["max_questions"] = 1
    config_copy["preferred_question_styles"].append("Dato solo en una copia")
    job_copy = setup.job_dict()
    job_copy["requirements"].append("Requisito solo de una copia")
    job_copy["seniority_expectations"]["not_required"].clear()

    assert setup.config_dict() == expected_config
    assert setup.job_dict() == expected_job


def test_setup_fields_cannot_be_reassigned(documents):
    setup = load_documents(documents)

    with pytest.raises(FrozenInstanceError):
        setup.candidate = None


def test_new_loads_and_snapshots_do_not_share_mutable_state(documents):
    first = load_documents(documents)
    expected = first.config_dict()
    changed = load_json(documents["config"])
    changed["max_questions"] = 10
    write_json(documents["config"], changed)

    second = load_documents(documents)

    assert first.config_dict() == expected
    assert second.config_dict()["max_questions"] == 10
    assert first.candidate is not second.candidate


def test_job_snapshot_survives_external_changes(documents):
    setup = load_documents(documents)
    expected = setup.job_dict()
    changed = load_json(documents["job"])
    changed["title"] = "Cambio posterior de prueba"
    write_json(documents["job"], changed)

    assert setup.job_dict() == expected


def test_default_files_do_not_depend_on_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    setup = load_interview_setup()

    assert setup.candidate.candidate_id == "cand-001"
    assert setup.job_dict()["job_id"] == "puesto-dev-junior-001"


def test_detects_candidate_change_while_loading_job(documents, monkeypatch):
    original_load = config_module.load_json

    def load_then_change_candidate(path):
        data = original_load(path)
        if Path(path) == documents["job"]:
            source = documents["candidate"]
            source.write_bytes(source.read_bytes() + b"\n")
        return data

    monkeypatch.setattr(config_module, "load_json", load_then_change_candidate)

    with pytest.raises(ProfileIntegrityError) as caught:
        load_documents(documents)

    assert caught.value.rule == "source_changed"


def test_repr_omits_full_config_job_and_candidate_contents(documents):
    setup = load_documents(documents)

    assert "preferred_question_styles" not in repr(setup)
    assert "Aplicaciones Nexo" not in repr(setup)
    assert "MesaFaro" not in repr(setup)

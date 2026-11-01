"""Contratos y fuentes del conjunto; no evalúa texto generado por un modelo."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json

import pytest

from harness.interview_config import load_interview_setup
from harness.json_loader import load_json
from harness.reference_cases import (
    DEFAULT_SCHEMA_PATH, DEFAULT_SUITE_PATH, ReferenceSuiteError,
    load_reference_suite, prepare_reference_cases, resolve_source_path,
)


@pytest.fixture
def source():
    return load_json(DEFAULT_SUITE_PATH), load_json(DEFAULT_SCHEMA_PATH), load_interview_setup()


def test_real_suite_resolves_approved_facts_and_keeps_five_steps_in_four_cases(source):
    data, schema, setup = source
    before = deepcopy(data)
    cases = prepare_reference_cases(data, schema, setup)
    assert len(cases) == 4 and sum(len(c["steps"]) for c in cases) == 5
    assert data["case_isolation"] == "new_session_per_case" and data["usage"] == "development_reference"
    assert [f["value"] for f in cases[0]["reference_facts"]] == ["Instituto Profesional Horizonte Digital", "Ingeniería en Informática"]
    assert [f["value"] for f in cases[1]["reference_facts"]] == [21, 3, 18, None]
    assert [f["value"] for f in cases[2]["reference_facts"]] == ["Inventario Aula", "Académico"]
    assert cases[3]["reference_facts"][0]["value"] == "Sin experiencia práctica con Kubernetes."
    assert cases[2]["steps"][1]["expected_fact_ids"] == ["fact-proyecto-nombre"]
    assert "value" not in data["cases"][0]["reference_facts"][0]
    assert data == before
    cases[0]["reference_facts"][0]["value"] = "Cambio de copia"
    assert data == before and setup.candidate.to_dict()["education"][0]["institution"] == "Instituto Profesional Horizonte Digital"


def test_loader_returns_independent_snapshots_and_hash_of_exact_file_bytes():
    suite = load_reference_suite()
    assert suite.source_path.is_absolute() and suite.suite_id == "consistencia-basica-001"
    assert suite.source_sha256 == hashlib.sha256(DEFAULT_SUITE_PATH.read_bytes()).hexdigest().upper()
    raw, resolved = suite.to_dict(), suite.resolved_cases()
    raw["cases"].clear()
    resolved[0]["reference_facts"][0]["value"] = "Otro"
    assert len(suite.to_dict()["cases"]) == 4
    assert suite.resolved_cases()[0]["reference_facts"][0]["value"] == "Instituto Profesional Horizonte Digital"
    with pytest.raises(FrozenInstanceError):
        suite.source_sha256 = "0" * 64


@pytest.mark.parametrize("path,value", [
    (("suite_version",), "2.0.0"),
    (("suite_id",), "consistencia-basica-001\n"),
    (("candidate_id",), "otro"),
    (("job_id",), "otro"),
    (("scenario_reference_date",), "2026-02-30"),
    (("candidate_source_sha256",), "0" * 64),
    (("review_mode",), "automatic_score"),
    (("usage",), "independent_holdout"),
    (("case_isolation",), "shared_session"),
    (("score",), 100),
    (("cases",), []),
    (("cases", 0, "case_id"), "cons-formacion\n"),
    (("cases", 0, "steps", 0, "question"), "  "),
    (("cases", 0, "steps", 0, "expected_fact_ids"), ["fact-inexistente"]),
    (("cases", 0, "steps", 0, "expected_fact_ids"), ["fact-institucion", "fact-institucion"]),
    (("cases", 0, "reference_facts", 0, "source"), "filesystem"),
    (("cases", 0, "reference_facts", 0, "path"), ["education", 99, "institution"]),
    (("cases", 0, "reference_facts", 0, "path"), ["education", "0", "institution"]),
    (("cases", 0, "reference_facts", 0, "path"), ["education", True, "institution"]),
    (("cases", 0, "reference_facts", 0, "value"), "CONTENIDO_RESERVADO"),
    (("cases", 2, "steps", 1, "step_number"), 3),
])
def test_invalid_contract_bindings_and_references_are_rejected(source, path, value):
    data, schema, setup = source
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ReferenceSuiteError) as caught:
        prepare_reference_cases(data, schema, setup)
    assert "CONTENIDO_RESERVADO" not in str(caught.value)


@pytest.mark.parametrize("kind", ["case", "fact", "unused_fact"])
def test_duplicate_ids_and_unused_reference_facts_are_rejected(source, kind):
    data, schema, setup = source
    if kind == "case":
        data["cases"][1]["case_id"] = data["cases"][0]["case_id"]
    elif kind == "fact":
        data["cases"][0]["reference_facts"][1]["fact_id"] = "fact-institucion"
    else:
        extra = deepcopy(data["cases"][0]["reference_facts"][0])
        extra.update(fact_id="fact-no-utilizado", path=["education", 0, "status"])
        data["cases"][0]["reference_facts"].append(extra)
    with pytest.raises(ReferenceSuiteError):
        prepare_reference_cases(data, schema, setup)


def test_case_steps_cannot_exceed_the_configured_session_limit(source, tmp_path):
    data, schema, setup = source
    path = tmp_path / "config.json"
    path.write_text(json.dumps(setup.config_dict() | {"max_questions": 1}), encoding="utf-8")
    limited = load_interview_setup(config_path=path)
    with pytest.raises(ReferenceSuiteError, match="límite"):
        prepare_reference_cases(data, schema, limited)


def test_source_null_is_valid_and_complex_values_are_copies():
    source = {"a/b": {"~x": [None, {"value": [1, 2]}]}}
    assert resolve_source_path(source, ["a/b", "~x", 0]) is None
    resolved = resolve_source_path(source, ["a/b", "~x", 1])
    resolved["value"].clear()
    assert source["a/b"]["~x"][1]["value"] == [1, 2]


@pytest.mark.parametrize("path", [[], ["missing"], ["items", -1], ["items", True], ["items", "0"]])
def test_invalid_source_paths_never_guess_or_evaluate_keys(path):
    with pytest.raises(ReferenceSuiteError):
        resolve_source_path({"items": ["dato"]}, path)


@pytest.mark.parametrize("raw", [b'{', b'{"suite_id":"a","suite_id":"b"}', b'{"value":NaN}'])
def test_strict_reader_rejects_bad_json_without_modifying_source(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    with pytest.raises(ReferenceSuiteError):
        load_reference_suite(path)
    assert path.read_bytes() == raw


def test_missing_files_and_invalid_schema_are_reported(source, tmp_path):
    with pytest.raises(ReferenceSuiteError, match="leer"):
        load_reference_suite(tmp_path / "missing.json")
    with pytest.raises(ReferenceSuiteError, match="leer"):
        load_reference_suite(schema_path=tmp_path / "missing-schema.json")
    data, _, setup = source
    with pytest.raises(ReferenceSuiteError, match="esquema"):
        prepare_reference_cases(data, {"type": "tipo-inexistente"}, setup)

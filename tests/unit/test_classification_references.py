"""Integridad de las 40 expectativas aprobadas; no mide un clasificador."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import re

import pytest

from harness.classification_contract import (
    ClassificationContractError, validate_classification_expectation,
)
from harness.classification_references import (
    DEFAULT_REFERENCES_PATH, ClassificationReferencesError,
    load_classification_references, prepare_classification_references,
)
from harness.json_loader import load_json


ROOT = Path(__file__).resolve().parents[2]
KNOWN_CHECK_IDS = {"R09", "R10", "R17", "R23", "R24", "R25", "R29", "R30", "R39", "R40"}
APPROVED_CASES_SHA256 = "b159f61b67cdb5561cb5ef22e67cf5cc1935cc49792f353ae17a3907d944e371"


@pytest.fixture(scope="module")
def source():
    return load_json(DEFAULT_REFERENCES_PATH)


def test_frozen_cases_and_assignments_match_approved_version(source):
    canonical = json.dumps(source["cases"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == APPROVED_CASES_SHA256
    suite = load_classification_references()
    assert len(suite.cases()) == 30
    check_ids = {case["case_id"] for case in suite.cases(split="comprobacion_conocida")}
    assert check_ids == KNOWN_CHECK_IDS
    assert not {case["case_id"] for case in suite.cases()} & check_ids
    assert source["approval"]["decision"] == "Apruebo"


def test_every_original_text_matches_approved_table_including_empty_and_spaces(source):
    document = (ROOT / "docs/clasificador.md").read_text(encoding="utf-8")
    section_start = '<a name="referencias-clasificacion-propuesta"></a>'
    assert section_start in document
    table = document.split(section_start, 1)[1].split('<a name="', 1)[0]
    originals = {}
    for line in table.splitlines():
        if re.match(r"^\| R\d{2} \|", line):
            fields = [value.strip() for value in line.strip("|").split("|")]
            originals[fields[0]] = fields[1]
    originals.update(R37="", R38="   ")
    assert len(originals) == 40
    for case in source["cases"]:
        assert case["input"]["text"] == originals[case["case_id"]]
        assert case["expected"]["original_text"] == originals[case["case_id"]]


def test_all_expectations_pass_shared_contract_without_generated_metadata(source):
    original = deepcopy(source)
    prepared = prepare_classification_references(source)
    assert source == original and prepared == original
    generated_fields = {"method", "rule_ids", "validation_status", "technical_error"}
    for case in prepared["cases"]:
        assert not generated_fields & case["expected"].keys()
        for unit in case["expected"]["units"]:
            assert not generated_fields & unit.keys()
    assert sum(c["expected"]["evaluability"] == "no_evaluable" for c in prepared["cases"]) == 8
    assert sum(len(c["expected"]["units"]) for c in prepared["cases"]) == 36
    prepared["cases"].clear()
    assert source == original


def test_uncertainty_and_global_hierarchy_preserve_approved_distinctions(source):
    cases = {case["case_id"]: case["expected"] for case in source["cases"]}
    assert cases["R08"]["classification"]["main_approach"] == "conductual"
    assert cases["R08"]["classification"]["main_form"] == "cerrada"
    assert cases["R21"]["classification"]["certainty"] == "indeterminada"
    assert cases["R24"]["classification"]["main_approach"] == "indeterminado"
    assert cases["R24"]["classification"]["certainty"] == "ambigua"
    assert cases["R25"]["classification"]["main_approach"] == "situacional"
    assert cases["R25"]["classification"]["certainty"] == "ambigua"
    for identifier in ("R26", "R27"):
        assert cases[identifier]["classification"]["main_approach"] is None
    assert len(cases["R28"]["units"]) == 1
    assert cases["R29"]["classification"]["main_approach"] == "situacional"
    assert cases["R29"]["classification"]["main_form"] is None
    assert cases["R29"]["units"][1]["depends_on"] == "u1"
    assert cases["R30"]["classification"]["secondary_approaches"] == ["factual_tecnico"]
    assert cases["R30"]["classification"]["main_approach_reason"]
    assert cases["R32"]["units"][0]["text"] == "¿Qué es una API?"


def test_model_input_excludes_expected_labels_notes_and_difficulty():
    suite = load_classification_references()
    data = suite.input_for("R03")
    assert set(data) == {"intervention_id", "text", "configuration", "context_turns", "competency"}
    assert data["configuration"]["approach"] == "conductual"
    assert suite.input_for("R01")["configuration"]["approach"] == "mixto"
    with pytest.raises(ValueError, match="grupo"):
        suite.input_for("R09")
    assert suite.input_for("R09", split="comprobacion_conocida")["intervention_id"] == "R09"


def test_contexts_and_snapshots_are_independent():
    suite = load_classification_references()
    data = suite.input_for("R08")
    data["context_turns"][0]["messages"][0]["content"] = "Cambio de copia"
    data["configuration"]["approach"] = "situacional"
    assert suite.input_for("R08")["context_turns"][0]["messages"][0]["content"] != "Cambio de copia"
    assert suite.input_for("R20")["context_turns"][0]["messages"][0]["content"].startswith("La coordinadora")
    assert suite.input_for("R21")["context_turns"] == []
    assert suite.input_for("R25", split="comprobacion_conocida")["context_turns"][0]["messages"][0]["role"] == "user"
    raw = suite.to_dict()
    raw["cases"].clear()
    assert len(suite.cases()) == 30
    with pytest.raises(FrozenInstanceError):
        suite.source_sha256 = "0" * 64
    assert suite.source_sha256 == hashlib.sha256(DEFAULT_REFERENCES_PATH.read_bytes()).hexdigest().upper()


@pytest.mark.parametrize("split", ["all", "reservado", "", None])
def test_unknown_split_cannot_bypass_explicit_selection(split):
    with pytest.raises(ValueError):
        load_classification_references().cases(split=split)


@pytest.mark.parametrize("kind", [
    "approval", "count", "duplicate_id", "split_count", "case_identity", "original_text",
    "label", "span", "secondary", "context_missing", "context_duplicate", "context_decimal",
    "context_limit", "context_system_role", "configuration", "competency", "contract_version",
    "new_field", "invalid_utf8",
])
def test_invalid_dataset_relationships_fail_safely(source, kind):
    data = deepcopy(source)
    first = data["cases"][0]
    context_case = data["cases"][7]
    if kind == "approval":
        data["approval"]["status"] = "pending"
    elif kind == "count":
        data["cases"].pop()
    elif kind == "duplicate_id":
        data["cases"][1]["case_id"] = "R01"
    elif kind == "split_count":
        first["split"] = "comprobacion_conocida"
    elif kind == "case_identity":
        first["expected"]["intervention_id"] = "R02"
    elif kind == "original_text":
        first["expected"]["original_text"] = "CONTENIDO_RESERVADO"
    elif kind == "label":
        first["expected"]["classification"]["attributes"] = ["CONTENIDO_RESERVADO"]
    elif kind == "span":
        first["expected"]["units"][0]["source_end"] = 10000
    elif kind == "secondary":
        data["cases"][29]["expected"]["classification"]["secondary_approaches"] = []
    elif kind == "context_missing":
        context_case["input"]["context_turns"] = []
    elif kind == "context_duplicate":
        context_case["input"]["context_turns"] *= 2
    elif kind == "context_decimal":
        context_case["input"]["context_turns"][0]["turn_number"] = 1.0
    elif kind == "context_limit":
        context_case["input"]["context_turns"][0]["turn_number"] = 20
    elif kind == "context_system_role":
        context_case["input"]["context_turns"][0]["messages"][0]["role"] = "system"
    elif kind == "configuration":
        first["input"]["configuration_overrides"]["max_questions"] = 99
    elif kind == "competency":
        first["input"]["competency"] = "Competencia inventada"
    elif kind == "contract_version":
        first["expected"]["contract_version"] = "2.0.0"
    elif kind == "new_field":
        first["score"] = 100
    else:
        first["context_note"] = "\ud800"
    with pytest.raises(ClassificationReferencesError) as caught:
        prepare_classification_references(data)
    assert "CONTENIDO_RESERVADO" not in str(caught.value)


@pytest.mark.parametrize(("level", "field", "value"), [
    ("root", "method", "llm"), ("root", "rule_ids", []),
    ("root", "validation_status", "validada"), ("root", "technical_error", None),
    ("unit", "method", "reglas"), ("unit", "rule_ids", ["R.TEST"]),
])
def test_reference_expectations_reject_fictitious_execution_metadata(source, level, field, value):
    data = deepcopy(source["cases"][0]["expected"])
    target = data if level == "root" else data["units"][0]
    target[field] = value
    with pytest.raises(ClassificationContractError):
        validate_classification_expectation(data, expected_intervention_id="R01", expected_text=data["original_text"])


def test_human_reference_cannot_claim_technical_fallback(source):
    data = deepcopy(source["cases"][0]["expected"])
    data["evaluability"] = None
    with pytest.raises(ClassificationContractError):
        validate_classification_expectation(data, expected_intervention_id="R01", expected_text=data["original_text"])


@pytest.mark.parametrize("raw", ['{"suite_version":"1.0.0","suite_version":"otra"}', '{"malformado":', '[]'])
def test_file_loader_rejects_duplicate_keys_malformed_json_and_wrong_shape(tmp_path, raw):
    path = tmp_path / "references.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ClassificationReferencesError):
        load_classification_references(path)
    assert path.read_text(encoding="utf-8") == raw


def test_loading_keeps_approved_sources_and_old_references_intact():
    paths = [ROOT / name for name in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "agent/agent.md", "config/interviews/basica.json", "data/reference_questions/consistencia_basica.json",
        "data/reference_questions/consistencia_ampliada.json", "data/reference_questions/clasificacion_basica.json",
    )]
    before = [path.read_bytes() for path in paths]
    load_classification_references()
    assert [path.read_bytes() for path in paths] == before

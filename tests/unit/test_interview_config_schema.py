"""Contrato de preferencias de entrevista y límites configurables."""

from pathlib import Path

import pytest

from harness.json_loader import load_json
from harness.schema_validator import DataValidationError, validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def config_pair():
    return (
        load_json(PROJECT_ROOT / "config/interviews/basica.json"),
        load_json(PROJECT_ROOT / "schemas/interview_config.schema.json"),
    )


def test_accepts_basic_configuration(config_pair):
    config, schema = config_pair

    assert validate_data(config, schema) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("modality", "laboral_general"),
        ("modality", "tecnica"),
        ("modality", "por_competencias"),
        ("approach", "conductual"),
        ("approach", "situacional"),
        ("approach", "mixto"),
        ("preferred_question_styles", ["abierta"]),
        ("preferred_question_styles", ["cerrada"]),
        ("preferred_question_styles", ["directiva"]),
        ("preferred_question_styles", ["abierta", "cerrada", "directiva"]),
        ("max_questions", 1),
        ("max_questions", 20),
    ],
)
def test_accepts_supported_preferences_and_limit_boundaries(config_pair, field, value):
    config, schema = config_pair
    config[field] = value

    assert validate_data(config, schema) is None


@pytest.mark.parametrize(
    "field",
    [
        "config_version", "config_id", "candidate_id", "job_id",
        "modality", "approach", "preferred_question_styles", "max_questions",
    ],
)
def test_requires_each_configuration_field(config_pair, field):
    config, schema = config_pair
    del config[field]

    with pytest.raises(DataValidationError) as caught:
        validate_data(config, schema)

    assert caught.value.rule == "required"
    assert field in str(caught.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("config_version", "2.0.0"),
        ("config_id", "cand-001"),
        ("candidate_id", "puesto-dev-junior-001"),
        ("job_id", "cand-001"),
        ("modality", "clinica"),
        ("approach", "sin_estructura"),
        ("preferred_question_styles", []),
        ("preferred_question_styles", ["abierta", "abierta"]),
        ("preferred_question_styles", ["mixto"]),
        ("preferred_question_styles", "abierta"),
        ("max_questions", -1),
        ("max_questions", 0),
        ("max_questions", 21),
        ("max_questions", 1.5),
        ("max_questions", "20"),
        ("max_questions", True),
    ],
)
def test_rejects_invalid_preferences_and_limits(config_pair, field, value):
    config, schema = config_pair
    config[field] = value

    with pytest.raises(DataValidationError):
        validate_data(config, schema)


def test_reports_upper_question_limit_with_field_and_clear_message(config_pair):
    config, schema = config_pair
    config["max_questions"] = 21

    with pytest.raises(DataValidationError) as caught:
        validate_data(config, schema)

    assert caught.value.path == "/max_questions"
    assert caught.value.rule == "maximum"
    assert "máximo permitido" in str(caught.value)


def test_rejects_undeclared_evaluation_settings(config_pair):
    config, schema = config_pair
    config["scoring"] = True

    with pytest.raises(DataValidationError) as caught:
        validate_data(config, schema)

    assert caught.value.rule == "additionalProperties"


def test_schema_alone_does_not_check_if_referenced_candidate_exists(config_pair):
    config, schema = config_pair
    config["candidate_id"] = "cand-999"

    assert validate_data(config, schema) is None

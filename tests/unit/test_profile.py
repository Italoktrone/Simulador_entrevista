"""Reglas de coherencia sobre copias en memoria del candidato aprobado."""

import copy
from pathlib import Path

import pytest

from harness.json_loader import load_json
from harness.profile import ProfileConsistencyError, validate_profile_data
from harness.schema_validator import DataValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def profile_pair():
    return (
        load_json(PROJECT_ROOT / "data/candidates/candidato_junior.json"),
        load_json(PROJECT_ROOT / "schemas/candidate.schema.json"),
    )


def test_accepts_approved_profile_without_mutating_inputs(profile_pair):
    profile, schema = profile_pair
    before = copy.deepcopy((profile, schema))

    assert validate_profile_data(profile, schema) is None

    assert (profile, schema) == before


@pytest.mark.parametrize(
    ("keys", "value", "path", "rule"),
    [
        (("scenario_reference_date",), "2026-02-31", "/scenario_reference_date", "invalid_date"),
        (("scenario_reference_date",), "2027-02-29", "/scenario_reference_date", "invalid_date"),
        (("education", 0, "start_month"), "0000-03", "/education/0/start_month", "invalid_month"),
        (("education", 0, "start_month"), "2026-03", "/education/0", "reversed_period"),
        (("education", 0, "graduation_month"), "2025-11", "/education/0/graduation_month", "graduation_before_end"),
        (("education", 0, "graduation_month"), "2027-01", "/education/0/graduation_month", "future_graduation"),
        (("work_experience", 0, "roles", 1, "end_month"), "2027-01", "/work_experience/0/roles/1", "future_period"),
        (("projects", 0, "end_month"), "2027-01", "/projects/0", "future_period"),
        (("projects", 0, "start_month"), "2025-03", "/projects/0", "project_outside_context"),
        (("projects", 1, "start_month"), "2021-08", "/projects/1", "project_outside_context"),
        (("projects", 1, "project_id"), "proj-001", "/projects/1/project_id", "duplicate_id"),
        (("work_experience", 0, "roles", 1, "role_id"), "role-001", "/work_experience/0/roles/1/role_id", "duplicate_id"),
        (("behavioral_situations", 1, "situation_id"), "S1", "/behavioral_situations/1/situation_id", "duplicate_id"),
        (("achievements", 1, "achievement_id"), "ach-001", "/achievements/1/achievement_id", "duplicate_id"),
        (("projects", 0, "experience_id"), "exp-999", "/projects/0/experience_id", "missing_reference"),
        (("projects", 0, "role_id"), "role-999", "/projects/0/role_id", "missing_reference"),
        (("projects", 0, "role_id"), "role-001", "/projects/0", "project_outside_context"),
        (("projects", 1, "education_id"), "edu-999", "/projects/1/education_id", "missing_reference"),
        (("education", 0, "final_project_id"), "proj-999", "/education/0/final_project_id", "missing_reference"),
        (("education", 0, "final_project_id"), "proj-001", "/education/0/final_project_id", "reference_mismatch"),
        (("work_experience", 0, "roles", 1, "project_ids", 0), "proj-999", "/work_experience/0/roles/1/project_ids/0", "missing_reference"),
        (("work_experience", 0, "roles", 1, "project_ids", 0), "proj-002", "/work_experience/0/roles/1/project_ids/0", "reference_mismatch"),
        (("behavioral_situations", 0, "project_id"), "proj-999", "/behavioral_situations/0/project_id", "missing_reference"),
        (("achievements", 0, "project_id"), "proj-999", "/achievements/0/project_id", "missing_reference"),
        (("achievements", 1, "situation_id"), "S999", "/achievements/1/situation_id", "missing_reference"),
        (("achievements", 1, "project_id"), "proj-002", "/achievements/1", "reference_mismatch"),
        (("professional_competencies", 0, "situation_ids", 0), "S999", "/professional_competencies/0/situation_ids/0", "missing_reference"),
        (("strengths", 0, "situation_ids", 0), "S999", "/strengths/0/situation_ids/0", "missing_reference"),
        (("improvement_areas", 0, "situation_ids", 0), "S999", "/improvement_areas/0/situation_ids/0", "missing_reference"),
        (("work_experience", 0, "roles", 1, "schedule_periods", 0, "start_month"), "2025-05", "/work_experience/0/roles/1/schedule_periods", "schedule_boundaries"),
        (("work_experience", 0, "roles", 1, "schedule_periods", 1, "end_month"), "2026-08", "/work_experience/0/roles/1/schedule_periods", "schedule_boundaries"),
        (("work_experience", 0, "roles", 1, "schedule_periods", 0, "end_month"), "2025-11", "/work_experience/0/roles/1/schedule_periods/1/start_month", "schedule_gap"),
        (("work_experience", 0, "roles", 1, "schedule_periods", 0, "end_month"), "2026-01", "/work_experience/0/roles/1/schedule_periods/1/start_month", "schedule_overlap"),
    ],
)
def test_rejects_incompatible_data_without_changing_it(profile_pair, keys, value, path, rule):
    profile, schema = profile_pair
    node = profile
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    before = copy.deepcopy((profile, schema))

    with pytest.raises(ProfileConsistencyError) as caught:
        validate_profile_data(profile, schema)

    assert caught.value.path == path
    assert caught.value.rule == rule
    assert (profile, schema) == before


def test_validates_structure_before_accessing_profile_fields(profile_pair):
    profile, schema = profile_pair
    del profile["education"]

    with pytest.raises(DataValidationError):
        validate_profile_data(profile, schema)


def test_accepts_real_leap_day_after_known_events(profile_pair):
    profile, schema = profile_pair
    profile["scenario_reference_date"] = "2028-02-29"

    assert validate_profile_data(profile, schema) is None


def test_uses_scenario_month_without_inventing_day_precision(profile_pair):
    profile, schema = profile_pair
    profile["scenario_reference_date"] = "2026-09-01"

    assert validate_profile_data(profile, schema) is None


def test_accepts_unsorted_schedules_without_reordering_input(profile_pair):
    profile, schema = profile_pair
    profile["work_experience"][0]["roles"][1]["schedule_periods"].reverse()
    before = copy.deepcopy(profile)

    validate_profile_data(profile, schema)

    assert profile == before


def test_checks_role_ownership_not_just_existence(profile_pair):
    profile, schema = profile_pair
    profile["work_experience"].append({
        "experience_id": "exp-002",
        "organization": "Organización solo de prueba",
        "team_context": "Equipo de prueba",
        "authority_limits": ["Con supervisión"],
        "roles": [{
            "role_id": "role-003", "title": "Cargo de prueba",
            "start_month": "2025-04", "end_month": "2026-09",
            "responsibilities": ["Tarea de prueba"],
        }],
    })
    profile["projects"][0]["experience_id"] = "exp-002"

    with pytest.raises(ProfileConsistencyError) as caught:
        validate_profile_data(profile, schema)

    assert caught.value.rule == "reference_mismatch"
    assert caught.value.path == "/projects/0/role_id"


def test_checks_reciprocal_project_link_when_role_declares_projects(profile_pair):
    profile, schema = profile_pair
    project = copy.deepcopy(profile["projects"][0])
    project["project_id"] = "proj-003"
    profile["projects"].append(project)

    with pytest.raises(ProfileConsistencyError) as caught:
        validate_profile_data(profile, schema)

    assert caught.value.rule == "reference_mismatch"
    assert caught.value.path == "/work_experience/0/roles/1/project_ids"

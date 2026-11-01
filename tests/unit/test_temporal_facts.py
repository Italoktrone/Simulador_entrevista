"""Duración calendario, jornadas y términos conjuntos de estudios/proyectos."""

from copy import deepcopy

import pytest

from harness.interview_config import load_interview_setup
from harness.temporal_facts import _months, build_temporal_facts, format_temporal_reference


def test_real_profile_has_twenty_one_months_with_role_and_schedule_breakdown():
    setup = load_interview_setup()
    source = setup.candidate.to_dict()
    before = deepcopy(source)
    facts = build_temporal_facts(source)
    employment = facts["employment"]
    assert employment["distinct_calendar_months"] == 21
    assert employment["full_time_equivalent_months"] is None
    internship, junior = employment["roles"]
    assert (internship["title"], internship["calendar_months"]) == ("Practicante de desarrollo", 3)
    assert internship["schedule_periods"] == []
    assert internship["months_without_recorded_schedule"] == 3
    assert (junior["title"], junior["calendar_months"]) == ("Desarrollador Junior", 18)
    assert junior["schedule_periods"] == [
        {"schedule": "Jornada parcial", "start_month": "2025-04", "end_month": "2025-12", "calendar_months": 9},
        {"schedule": "Jornada completa", "start_month": "2026-01", "end_month": "2026-09", "calendar_months": 9},
    ]
    assert junior["months_without_recorded_schedule"] == 0
    assert source == before
    setup.candidate.assert_source_unchanged()


@pytest.mark.parametrize("start, end, count", [
    ("2025-01", "2026-09", 21),
    ("2025-04", "2026-09", 18),
    ("2025-12", "2026-01", 2),
    ("2025-02", "2025-02", 1),
])
def test_months_include_both_ends_and_cross_years(start, end, count):
    assert len(_months(start, end)) == count


def test_concurrent_employer_does_not_increase_distinct_calendar_months():
    source = load_interview_setup().candidate.to_dict()
    source["work_experience"].append({
        "organization": "Otra organización ficticia",
        "roles": [{"role_id": "otro", "title": "Apoyo", "start_month": "2025-02", "end_month": "2025-04"}],
    })
    employment = build_temporal_facts(source)["employment"]
    assert sum(role["calendar_months"] for role in employment["roles"]) == 24
    assert employment["distinct_calendar_months"] == 21


def test_academic_project_is_not_added_to_employment_duration():
    source = load_interview_setup().candidate.to_dict()
    source["projects"][1]["start_month"] = "2024-08"
    assert build_temporal_facts(source)["employment"]["distinct_calendar_months"] == 21


def test_completion_events_include_all_projects_and_both_education_dates():
    source = load_interview_setup().candidate.to_dict()
    source["education"][0]["graduation_month"] = "2026-01"
    events = build_temporal_facts(source)["completion_events"]
    assert [(event["event_type"], event["record_id"], event["month"]) for event in events] == [
        ("project_end", "proj-002", "2025-11"),
        ("education_end", "edu-001", "2025-12"),
        ("graduation", "edu-001", "2026-01"),
        ("project_end", "proj-001", "2026-09"),
    ]


def test_readable_reference_has_total_and_complete_finish_order_without_inventing_schedule():
    facts = build_temporal_facts(load_interview_setup().candidate.to_dict())
    text = format_temporal_reference(facts)
    assert "Experiencia laboral total: 21 meses calendario distintos" in text
    assert "Sin jornada especificada en el perfil: 3 meses" in text
    assert "Jornada parcial: 2025-04 a 2025-12, 9 meses" in text
    assert "Jornada completa: 2026-01 a 2026-09, 9 meses" in text
    assert "No calculable" in text
    assert text.index('2025-11: Término de proyecto "Inventario Aula"') < text.index("2025-12: Término de estudios")
    assert text.index("2025-12: Titulación") < text.index('2026-09: Término de proyecto "MesaFaro"')


def test_input_order_and_output_edits_do_not_change_source_or_event_order():
    source = load_interview_setup().candidate.to_dict()
    original = build_temporal_facts(source)
    source["work_experience"][0]["roles"].reverse()
    source["projects"].reverse()
    before = deepcopy(source)
    facts = build_temporal_facts(source)
    assert facts == original
    facts["employment"]["roles"][0]["title"] = "Cambio local"
    facts["completion_events"][0]["name"] = "Otro nombre"
    assert source == before

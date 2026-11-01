"""Fechas del perfil: orden, solapamientos y separación del historial."""

from copy import deepcopy
import json

import pytest

from harness.interview_config import load_interview_setup
from harness.prompt_builder import (
    SCENARIO_DATA_MARKER, SCENARIO_END_MARKER, CHRONOLOGY_DATA_MARKER, TEMPORAL_DATA_MARKER, _project_chronology,
    build_messages, load_instructions,
)


def test_context_preserves_real_dates_and_reports_contained_overlap():
    setup = load_interview_setup()
    original = setup.candidate.to_dict()
    messages = build_messages(setup, "Ordena los proyectos.", instructions=load_instructions())
    raw = messages[0]["content"].split(SCENARIO_DATA_MARKER, 1)[1].split(SCENARIO_END_MARKER, 1)[0]
    scenario = json.loads(raw)
    assert scenario["project_chronology"] == {
        "by_start_month": [
            {"project_id": "proj-001", "name": "MesaFaro", "start_month": "2025-04", "end_month": "2026-09"},
            {"project_id": "proj-002", "name": "Inventario Aula", "start_month": "2025-08", "end_month": "2025-11"},
        ],
        "by_end_month": [
            {"project_id": "proj-002", "name": "Inventario Aula", "start_month": "2025-08", "end_month": "2025-11"},
            {"project_id": "proj-001", "name": "MesaFaro", "start_month": "2025-04", "end_month": "2026-09"},
        ],
        "overlaps": [{
            "projects": [
                {"project_id": "proj-001", "name": "MesaFaro"},
                {"project_id": "proj-002", "name": "Inventario Aula"},
            ],
            "start_month": "2025-08", "end_month": "2025-11",
        }],
    }
    assert scenario["candidate_profile"] == original == setup.candidate.to_dict()
    assert messages[0]["content"].split(CHRONOLOGY_DATA_MARKER, 1)[1].split(TEMPORAL_DATA_MARKER, 1)[0] == (
        'Hechos del perfil por mes; las posiciones con el mismo mes no indican orden dentro de él.\n'
        'Orden por INICIO:\n- 2025-04: "MesaFaro".\n- 2025-08: "Inventario Aula".\n'
        'Orden por TÉRMINO:\n- 2025-11: "Inventario Aula".\n- 2026-09: "MesaFaro".\n'
        'Solapamientos entre periodos:\n- "MesaFaro" y "Inventario Aula": de 2025-08 a 2025-11.'
    )
    setup.candidate.assert_source_unchanged()


def test_input_order_or_wrong_history_cannot_rewrite_authorized_chronology():
    setup = load_interview_setup()
    candidate = setup.candidate.to_dict()
    before = deepcopy(candidate)
    expected = _project_chronology(candidate)
    candidate["projects"].reverse()
    actual = _project_chronology(candidate)
    assert actual == expected
    actual["by_start_month"][0]["name"] = "Cambio en la copia"
    assert candidate["projects"] == list(reversed(before["projects"]))
    assert setup.candidate.to_dict() == before

    instructions = load_instructions()
    baseline = build_messages(setup, "Pregunta", instructions=instructions)
    history = [
        {"role": "user", "content": "¿Cuál realizaste primero?"},
        {"role": "assistant", "content": "Primero Inventario Aula y después MesaFaro."},
    ]
    with_history = build_messages(setup, "¿Mantienes ese orden?", instructions=instructions, history=history)
    assert with_history[0] == baseline[0]
    assert with_history[1:3] == history


@pytest.mark.parametrize("first_start, first_end, second_start, second_end, expected", [
    ("2025-04", "2025-06", "2025-07", "2025-11", None),
    ("2025-04", "2025-08", "2025-08", "2025-11", ("2025-08", "2025-08")),
    ("2025-04", "2026-09", "2025-08", "2025-11", ("2025-08", "2025-11")),
    ("2025-10", "2026-03", "2025-12", "2026-05", ("2025-12", "2026-03")),
    ("2026-01", "2026-05", "2025-12", "2026-01", ("2026-01", "2026-01")),
])
def test_month_ranges_handle_separation_boundaries_containment_and_year_changes(
    first_start, first_end, second_start, second_end, expected,
):
    source = {"projects": [
        {"project_id": "a", "name": "Uno", "start_month": first_start, "end_month": first_end},
        {"project_id": "b", "name": "Dos", "start_month": second_start, "end_month": second_end},
    ]}
    before = deepcopy(source)
    chronology = _project_chronology(source)
    assert [item["start_month"] for item in chronology["by_start_month"]] == sorted([first_start, second_start])
    assert [item["end_month"] for item in chronology["by_end_month"]] == sorted([first_end, second_end])
    if expected is None:
        assert chronology["overlaps"] == []
    else:
        assert len(chronology["overlaps"]) == 1
        overlap = chronology["overlaps"][0]
        assert (overlap["start_month"], overlap["end_month"]) == expected
        assert {item["project_id"] for item in overlap["projects"]} == {"a", "b"}
    assert source == before


def test_same_start_month_is_preserved_without_inventing_days_or_changing_source():
    source = {"projects": [
        {"project_id": "b", "name": "Segundo", "start_month": "2025-03", "end_month": "2025-06"},
        {"project_id": "a", "name": "Primero", "start_month": "2025-03", "end_month": "2025-04"},
    ]}
    chronology = _project_chronology(source)
    assert [item["start_month"] for item in chronology["by_start_month"]] == ["2025-03", "2025-03"]
    assert {item["project_id"] for item in chronology["by_start_month"]} == {"a", "b"}
    assert chronology["overlaps"][0]["start_month"] == "2025-03"
    assert chronology["overlaps"][0]["end_month"] == "2025-04"

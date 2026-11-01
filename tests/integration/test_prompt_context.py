"""Preparación del contexto desde archivos reales, sin consultar al LLM."""

from pathlib import Path
import json

from harness.interview_config import load_interview_setup
from harness.prompt_builder import (
    SCENARIO_DATA_MARKER, SCENARIO_END_MARKER, CHRONOLOGY_DATA_MARKER,
    build_messages, load_instructions,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_prepares_initial_context_and_preserves_all_source_files():
    paths = [
        PROJECT_ROOT / "agent/agent.md",
        PROJECT_ROOT / "config/interviews/basica.json",
        PROJECT_ROOT / "data/candidates/candidato_junior.json",
        PROJECT_ROOT / "data/jobs/desarrollador_junior.json",
    ]
    before = [path.read_bytes() for path in paths]
    setup = load_interview_setup()
    instructions = load_instructions()

    messages = build_messages(setup, "¿Dónde estudiaste?", instructions=instructions)

    assert [message["role"] for message in messages] == ["system", "user"]
    assert messages[1]["content"] == "¿Dónde estudiaste?"
    assert "Instituto Profesional Horizonte Digital" in messages[0]["content"]
    assert "Aplicaciones Nexo" in messages[0]["content"]
    assert "entrevista-basica-001" in messages[0]["content"]
    scenario = json.loads(messages[0]["content"].split(SCENARIO_DATA_MARKER, 1)[1].split(SCENARIO_END_MARKER, 1)[0])
    assert [project["name"] for project in scenario["project_chronology"]["by_start_month"]] == [
        "MesaFaro", "Inventario Aula",
    ]
    assert scenario["project_chronology"]["overlaps"][0]["start_month"] == "2025-08"
    assert scenario["project_chronology"]["overlaps"][0]["end_month"] == "2025-11"
    assert messages[0]["content"].split(CHRONOLOGY_DATA_MARKER, 1)[0].endswith(SCENARIO_END_MARKER + instructions)
    assert scenario["temporal_facts"]["employment"]["distinct_calendar_months"] == 21
    assert scenario["literal_name_references"]["/candidate_profile/education/0/institution"] == (
        setup.candidate.to_dict()["education"][0]["institution"]
    )
    assert setup.candidate.assert_source_unchanged() is None
    assert [path.read_bytes() for path in paths] == before

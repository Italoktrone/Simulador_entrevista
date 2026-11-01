"""Datos temporales calculados desde el perfil, separados de respuestas previas."""

import json

from harness.interview_config import load_interview_setup
from harness.prompt_builder import (
    SCENARIO_DATA_MARKER, SCENARIO_END_MARKER, TEMPORAL_DATA_MARKER,
    CHRONOLOGY_DATA_MARKER, build_messages, load_instructions,
)


def test_real_context_keeps_correct_totals_and_completion_events_with_incorrect_history():
    setup = load_interview_setup()
    source_before = setup.candidate.source_path.read_bytes()
    instructions = load_instructions()
    history = [
        {"role": "user", "content": "¿Cuánto trabajaste?"},
        {"role": "assistant", "content": "Un año y medio en total, incluyendo la práctica."},
    ]
    baseline = build_messages(setup, "Pregunta", instructions=instructions)
    messages = build_messages(setup, "¿Confirmas ese total?", instructions=instructions, history=history)
    assert messages[0] == baseline[0]
    assert messages[1:3] == history
    raw = messages[0]["content"].split(SCENARIO_DATA_MARKER, 1)[1].split(SCENARIO_END_MARKER, 1)[0]
    facts = json.loads(raw)["temporal_facts"]
    assert facts["employment"]["distinct_calendar_months"] == 21
    assert [(event["record_id"], event["month"]) for event in facts["completion_events"]] == [
        ("proj-002", "2025-11"), ("edu-001", "2025-12"),
        ("edu-001", "2025-12"), ("proj-001", "2026-09"),
    ]
    readable = messages[0]["content"].split(TEMPORAL_DATA_MARKER, 1)[1].split(CHRONOLOGY_DATA_MARKER, 1)[0]
    assert "21 meses calendario" in readable and "No calculable" in readable
    assert setup.candidate.source_path.read_bytes() == source_before
    setup.candidate.assert_source_unchanged()

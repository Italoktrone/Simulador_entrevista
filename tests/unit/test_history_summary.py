"""Citas por índices, procedencia y copias; no certifica relevancia semántica."""

from copy import deepcopy
import json

import pytest

from harness.history_summary import (
    HistorySummaryError, assemble_summary, build_selection_messages, build_summary_source,
    generate_summary, parse_selection, validate_summary,
)
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse, LLMTimeoutError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime


class Client:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.requests = []

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        result = next(self.outcomes)
        if isinstance(result, BaseException):
            raise result
        return result


def answer(text, **changes):
    return LLMResponse(text, "simulado", "ollama", 0.1, **changes)


@pytest.fixture
def session():
    client = Client([
        answer("Inventario Aula fue académico. Usé Python y PostgreSQL. Esta frase introduce el tema de la respuesta. No tuvo clientes comerciales."),
        LLMTimeoutError("DETALLE_RESERVADO"),
        answer("MesaFaro comenzó en abril de 2025. Colaboré en endpoints bajo supervisión. Esta frase sirve de introducción general. No administré producción."),
        answer("Trabajé 21 meses calendario. Incluye 3 de práctica y 18 como junior."),
        answer("Fueron nueve meses parciales y nueve completos."),
    ])
    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), client)
    for question in ("Proyecto académico", "PREGUNTA_FALLIDA", "Proyecto profesional", "Duración total", "Jornadas"):
        try:
            runtime.ask(question)
        except LLMTimeoutError:
            pass
    runtime.close("user_exit")
    return runtime.session_dict()


def choices():
    return [{"question_number": 1, "segment_indices": [1, 4]}, {"question_number": 3, "segment_indices": [1, 4]}]


def test_generated_summary_uses_exact_quotes_preserves_recent_turns_and_does_not_mutate_source(session):
    before = deepcopy(session)
    client = Client([answer(json.dumps({"selections": choices()}), finish_reason="stop")])
    summary, response = generate_summary(session, client)
    validate_summary(summary, session)
    assert summary["review_status"] == "not_reviewed" and summary["summary_version"] == "1.0.0"
    assert summary["configuration"] == session["configuration"]
    assert [t["question_number"] for t in summary["older_turns"]] == [1, 3]
    assert [t["question_number"] for t in summary["recent_turns"]] == [4, 5]
    assert summary["older_turns"][0]["quotes"] == [
        {"segment_index": 1, "text": "Inventario Aula fue académico."},
        {"segment_index": 2, "text": "Usé Python y PostgreSQL."},
        {"segment_index": 4, "text": "No tuvo clientes comerciales."},
    ]
    assert summary["older_turns"][1]["quotes"][-1]["text"] == "No administré producción."
    assert summary["older_turns"][0]["omitted_segment_indices"] == [3]
    assert summary["older_turns"][0]["policy_added_segment_indices"] == [2]
    assert summary["recent_turns"][0]["answer"] == session["attempts"][3]["response"]["text"]
    assert summary["statistics"]["omitted_segments"] == 2
    assert len(client.requests) == 1 and response.finish_reason == "stop"
    assert session == before
    summary["configuration"]["max_questions"] = 1
    summary["recent_turns"][0]["answer"] = "Cambio de copia"
    assert session == before


def test_selector_receives_only_older_completed_turns_as_untrusted_user_data(session):
    source = build_summary_source(session)
    before = deepcopy(source)
    messages = build_selection_messages(source)
    assert [m["role"] for m in messages] == ["system", "user"]
    data = json.loads(messages[1]["content"])
    assert [t["question_number"] for t in data["old_turns"]] == [1, 3]
    assert "PREGUNTA_FALLIDA" not in str(messages) and "DETALLE_RESERVADO" not in str(messages)
    assert "Trabajé 21 meses" not in str(messages) and "candidate_profile" not in str(messages)
    assert "candidate_source_sha256" not in str(messages) and "configuration" not in data
    messages[1]["content"] = "Cambio del cliente"
    assert source == before


@pytest.mark.parametrize("choice", [
    [], choices()[::-1], choices()[:1],
    [{"question_number": True, "segment_indices": [1]}, choices()[1]],
    [{"question_number": 1, "segment_indices": []}, choices()[1]],
    [{"question_number": 1, "segment_indices": [1, 1]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [1, 3, 2]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [0, 1]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [1, 5]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [True]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [1.0]}, choices()[1]],
    [{"question_number": 1, "segment_indices": ["1"]}, choices()[1]],
    [{"question_number": 1, "segment_indices": [1], "text": "INVENTADO"}, choices()[1]],
])
def test_invalid_selections_cannot_change_order_sources_or_add_free_text(session, choice):
    with pytest.raises(HistorySummaryError) as caught:
        assemble_summary(build_summary_source(session), choice)
    assert "INVENTADO" not in str(caught.value)


@pytest.mark.parametrize("text", [
    "{JSON roto", '```json\n{"selections":[]}\n```', '[]', '{"otra_clave":[]}',
    '{"selections":[],"texto":"INVENTADO"}', '{"selections":null}',
    '{"selections":[],"selections":[]}',
    '{"selections":[{"question_number":1,"question_number":2,"segment_indices":[1]}]}',
])
def test_model_output_must_be_strict_json_without_duplicate_fields(text):
    with pytest.raises(HistorySummaryError) as caught:
        parse_selection(text)
    assert "INVENTADO" not in str(caught.value)


@pytest.mark.parametrize(("path", "value"), [
    (("source_session_id",), "otra-sesion"),
    (("source_history_sha256",), "0" * 64),
    (("candidate_source_sha256",), "0" * 64),
    (("configuration", "max_questions"), 1),
    (("older_turns", 0, "question"), "Pregunta alterada"),
    (("older_turns", 0, "question_number"), True),
    (("older_turns", 0, "quotes", 0, "text"), "Inventario Aula fue profesional."),
    (("recent_turns", 0, "answer"), "Texto inventado"),
    (("statistics", "omitted_segments"), 0),
    (("review_status",), "approved"),
    (("extra",), "dato inesperado"),
])
def test_revalidation_detects_changed_citations_metadata_recent_turns_and_extra_fields(session, path, value):
    summary = assemble_summary(build_summary_source(session), choices())
    target = summary
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(HistorySummaryError):
        validate_summary(summary, session)


def test_revalidation_detects_later_source_changes(session):
    summary = assemble_summary(build_summary_source(session), choices())
    session["attempts"][0]["response"]["text"] += " Otra afirmación."
    with pytest.raises(HistorySummaryError):
        validate_summary(summary, session)


def test_policy_restores_anchors_even_if_selector_omits_first_and_negative_fragments(session):
    selected = [{"question_number": 1, "segment_indices": [2]}, {"question_number": 3, "segment_indices": [2]}]
    summary = assemble_summary(build_summary_source(session), selected)
    assert [q["segment_index"] for q in summary["older_turns"][0]["quotes"]] == [1, 2, 4]
    assert [q["segment_index"] for q in summary["older_turns"][1]["quotes"]] == [1, 2, 4]
    assert summary["older_turns"][0]["policy_added_segment_indices"] == [1, 4]
    assert summary["older_turns"][0]["omitted_segment_indices"] == [3]
    validate_summary(summary, session)


@pytest.mark.parametrize("middle", [
    "No tuvo clientes comerciales.", "Trabajé 21 meses.", "Usé Python y Flask.",
    "Colaboré bajo supervisión.", "Solo hice backend.", "No lo recuerdo con precisión.",
])
def test_numbers_negations_limits_and_capitalized_names_are_kept_by_policy(session, middle):
    session["attempts"][0]["response"]["text"] = f"Inicio de la respuesta. {middle} Cierre de la respuesta."
    source = build_summary_source(session)
    assert source["older_turns"][0]["required_segment_indices"] == [1, 2, 3]


@pytest.mark.parametrize("keep", [0, 21, True, "2"])
def test_invalid_recent_window_is_rejected(session, keep):
    with pytest.raises(HistorySummaryError):
        build_summary_source(session, keep_recent_pairs=keep)


@pytest.mark.parametrize("integrity", ["not_checked", "failed"])
def test_unverified_or_failed_profile_integrity_is_rejected(session, integrity):
    session["source_integrity"] = integrity
    with pytest.raises(HistorySummaryError):
        build_summary_source(session)


def test_small_or_empty_histories_do_not_call_a_model(session):
    client = Client([])
    summary, response = generate_summary(session, client, keep_recent_pairs=20)
    assert response is None and client.requests == [] and summary["older_turns"] == []
    assert len(summary["recent_turns"]) == 4
    session["attempts"] = []
    empty, response = generate_summary(session, None)
    assert empty["statistics"]["old_segments"] == 0 and empty["recent_turns"] == []


@pytest.mark.parametrize("outcome", [answer('{"selections":[]}', finish_reason="length"), LLMTimeoutError("Espera agotada")])
def test_cut_or_failed_selection_is_not_accepted_and_not_retried(session, outcome):
    before = deepcopy(session)
    client = Client([outcome])
    with pytest.raises(HistorySummaryError if isinstance(outcome, LLMResponse) else LLMTimeoutError):
        generate_summary(session, client)
    assert len(client.requests) == 1 and session == before

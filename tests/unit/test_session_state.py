"""Registro completo de intentos, tiempos, aislamiento y cierre, sin red."""

from copy import deepcopy
from datetime import datetime, timedelta
import json
from uuid import UUID

import pytest

from harness.application.cli import format_session, run_console
from harness.interview_config import load_interview_setup
from harness.llm.client import (
    LLMAuthenticationError, LLMInvalidResponseError, LLMProviderError,
    LLMResponse, LLMTimeoutError,
)
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import PromptBuildError, load_instructions
from harness.runtime import InterviewFinishedError, InterviewRuntime
from scripts import run_interview
from harness import session_log


def answer(text="Respuesta completa", **changes):
    values = dict(text=text, model="modelo-informado", provider="ollama", elapsed_seconds=0.2,
                  input_tokens=30, output_tokens=5, finish_reason="stop")
    return LLMResponse(**(values | changes))


class Client:
    def __init__(self, outcomes, action=None):
        self.outcomes = iter(outcomes)
        self.action = action
        self.requests = []

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        if self.action:
            self.action()
        result = next(self.outcomes)
        if isinstance(result, BaseException):
            raise result
        return result


@pytest.fixture
def setup():
    return load_interview_setup()


def runtime_for(setup, client):
    return InterviewRuntime(setup, load_instructions(), client, provider="ollama", model="modelo-solicitado")


def run_entries(runtime, entries):
    iterator = iter(entries)
    output = []

    def read(_):
        result = next(iterator)
        if isinstance(result, BaseException):
            raise result
        return result

    code = run_console(runtime, provider="ollama", model="simulado", input_fn=read, output_fn=output.append)
    return code, "\n".join(output)


def test_sessions_have_distinct_ids_real_utc_dates_and_separate_configuration(setup):
    first = runtime_for(setup, Client([]))
    second = runtime_for(setup, Client([]))
    snapshot = first.session_dict()
    assert UUID(first.session_id).version == UUID(second.session_id).version == 4
    assert first.session_id != second.session_id
    assert first.session_id != setup.config_dict()["config_id"]
    assert snapshot["candidate_id"] == "cand-001"
    assert snapshot["job_id"] == "puesto-dev-junior-001"
    assert snapshot["configuration"] == setup.config_dict()
    assert snapshot["candidate_source_sha256"] == setup.candidate.source_sha256
    assert snapshot["status"] == "open" and snapshot["closed_at"] is None
    assert snapshot["attempts"] == snapshot["issues"] == []
    assert datetime.fromisoformat(snapshot["created_at"]).utcoffset() == timedelta(0)
    assert json.loads(json.dumps(snapshot, ensure_ascii=False, allow_nan=False)) == snapshot


def test_exported_record_cannot_change_configuration_answers_or_context(setup):
    runtime = runtime_for(setup, Client([answer()]))
    runtime.ask("  Pregunta original\n")
    before = runtime.session_dict()
    copy = runtime.session_dict()
    copy["configuration"]["preferred_question_styles"].append("Otro estilo")
    copy["attempts"][0]["question"] = "Pregunta cambiada"
    copy["attempts"][0]["response"]["text"] = "Respuesta cambiada"
    copy["issues"].append({"code": "falso"})
    assert runtime.session_dict() == before
    assert runtime.history_messages() == [
        {"role": "user", "content": "  Pregunta original\n"},
        {"role": "assistant", "content": "Respuesta completa"},
    ]


def test_full_record_retains_errors_and_partial_text_without_promoting_them_to_history(setup):
    client = Client([answer("Primera respuesta"), LLMTimeoutError("Espera simulada"),
                     answer("PARCIAL_DIAGNOSTICO", finish_reason="length"), answer("Cuarta respuesta")])
    runtime = runtime_for(setup, client)
    runtime.ask("Primera")
    with pytest.raises(LLMTimeoutError):
        runtime.ask("Segunda fallida")
    with pytest.raises(LLMInvalidResponseError):
        runtime.ask("Tercera cortada")
    runtime.ask("Cuarta")
    attempts = runtime.session_dict()["attempts"]
    assert [row["question_number"] for row in attempts] == [1, 2, 3, 4]
    assert [row["status"] for row in attempts] == ["completed", "error", "incomplete", "completed"]
    assert [row["question"] for row in attempts] == ["Primera", "Segunda fallida", "Tercera cortada", "Cuarta"]
    assert attempts[1]["response"] is None
    assert attempts[1]["issues"][0]["code"] == "timeout"
    assert attempts[2]["response"]["text"] == "PARCIAL_DIAGNOSTICO"
    assert attempts[2]["response"]["finish_reason"] == "length"
    assert attempts[0]["response"]["input_tokens"] == 30
    assert runtime.questions_asked == len(client.requests) == 4
    assert client.requests[3][1:] == [
        {"role": "user", "content": "Primera"},
        {"role": "assistant", "content": "Primera respuesta"},
        {"role": "user", "content": "Cuarta"},
    ]
    for row in attempts:
        assert datetime.fromisoformat(row["requested_at"]).utcoffset() == timedelta(0)
        assert datetime.fromisoformat(row["finished_at"]).utcoffset() == timedelta(0)
    assert len(runtime.history_messages()) == 4


def test_invalid_question_creates_no_attempt_after_a_complete_turn(setup):
    client = Client([answer()])
    runtime = runtime_for(setup, client)
    runtime.ask("Primera")
    before = runtime.session_dict()
    with pytest.raises(PromptBuildError):
        runtime.ask(" \n")
    assert runtime.session_dict() == before and len(client.requests) == 1


def test_close_preserves_first_reason_timestamp_and_record(setup):
    runtime = runtime_for(setup, Client([answer()]))
    runtime.ask("Primera")
    runtime.close("user_exit")
    before = runtime.session_dict()
    runtime.close("interrupted")
    assert runtime.session_dict() == before
    assert before["status"] == "closed" and before["close_reason"] == "user_exit"
    assert datetime.fromisoformat(before["closed_at"]).utcoffset() == timedelta(0)
    with pytest.raises(InterviewFinishedError):
        runtime.ask("No debe registrarse")
    assert runtime.session_dict() == before


@pytest.mark.parametrize("outcome, expected_error, status, close_reason", [
    (answer(), None, "completed", "question_limit"),
    (LLMTimeoutError("Fallo"), LLMTimeoutError, "error", "question_limit"),
    (answer("Cortada", finish_reason="length"), LLMInvalidResponseError, "incomplete", "question_limit"),
    (KeyboardInterrupt(), KeyboardInterrupt, "interrupted", "interrupted"),
])
def test_last_attempt_finalizes_record_and_closes_with_limit_or_interrupt(
    setup, tmp_path, outcome, expected_error, status, close_reason,
):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(setup.config_dict() | {"max_questions": 1}), encoding="utf-8")
    limited_setup = load_interview_setup(config_path=config_path)
    runtime = runtime_for(limited_setup, Client([outcome]))
    if expected_error:
        with pytest.raises(expected_error):
            runtime.ask("Única pregunta")
    else:
        runtime.ask("Única pregunta")
    snapshot = runtime.session_dict()
    assert snapshot["status"] == "closed" and snapshot["close_reason"] == close_reason
    assert len(snapshot["attempts"]) == 1 and snapshot["attempts"][0]["status"] == status
    assert snapshot["attempts"][0]["finished_at"] is not None
    with pytest.raises(InterviewFinishedError):
        runtime.ask("Fuera del límite")
    assert runtime.questions_asked == 1


@pytest.mark.parametrize("provider_also_fails", [False, True])
def test_integrity_failure_keeps_all_incidents_and_rejects_that_answer(setup, tmp_path, provider_also_fails):
    path = tmp_path / "candidate.json"
    path.write_bytes(setup.candidate.source_path.read_bytes())
    copied_setup = load_interview_setup(candidate_path=path)
    second = LLMTimeoutError("Fallo simultáneo") if provider_also_fails else answer("NO_ACEPTAR")
    client = Client([answer("Primera válida"), second])
    runtime = runtime_for(copied_setup, client)
    runtime.ask("Primera")
    client.action = lambda: path.write_text("{}", encoding="utf-8")
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("Segunda")
    snapshot = runtime.session_dict()
    last = snapshot["attempts"][-1]
    assert snapshot["status"] == "closed" and snapshot["close_reason"] == "profile_integrity_error"
    assert last["status"] == "error" and last["finished_at"] is not None
    assert snapshot["source_integrity"] == "failed"
    assert [issue["code"] for issue in last["issues"]] == (
        ["timeout", "profile_integrity_error"] if provider_also_fails else ["profile_integrity_error"]
    )
    assert snapshot["issues"] == []
    assert len(runtime.history_messages()) == 2
    assert str(path) not in json.dumps(snapshot, ensure_ascii=False)
    setup.candidate.assert_source_unchanged()


def test_integrity_failure_before_dispatch_is_a_session_issue_without_a_question(setup, tmp_path):
    path = tmp_path / "candidate.json"
    path.write_bytes(setup.candidate.source_path.read_bytes())
    runtime = runtime_for(load_interview_setup(candidate_path=path), Client([]))
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("No enviada")
    snapshot = runtime.session_dict()
    assert snapshot["attempts"] == [] and runtime.questions_asked == 0
    assert snapshot["issues"][0]["code"] == "profile_integrity_error"
    assert snapshot["close_reason"] == "profile_integrity_error"


def test_interruption_is_recorded_and_programmatic_caller_can_continue_if_slots_remain(setup):
    runtime = runtime_for(setup, Client([answer("Uno"), KeyboardInterrupt(), answer("Tres")]))
    runtime.ask("Uno")
    with pytest.raises(KeyboardInterrupt):
        runtime.ask("Dos interrumpida")
    assert runtime.session_dict()["status"] == "open"
    assert runtime.session_dict()["attempts"][1]["status"] == "interrupted"
    runtime.ask("Tres")
    assert runtime.questions_asked == 3 and len(runtime.history_messages()) == 4


@pytest.mark.parametrize("error", [
    LLMTimeoutError("DETALLE_RESERVADO"), LLMAuthenticationError("DETALLE_RESERVADO"),
    LLMProviderError("DETALLE_RESERVADO"), ValueError("DETALLE_RESERVADO"),
])
def test_error_catalogue_does_not_copy_messages_causes_or_environment_credentials(setup, monkeypatch, error):
    monkeypatch.setenv("OPENAI_API_KEY", "CREDENCIAL_FICTICIA_NO_REGISTRAR")
    error.__cause__ = RuntimeError("Authorization: Bearer CREDENCIAL_FICTICIA_NO_REGISTRAR")
    runtime = runtime_for(setup, Client([error]))
    with pytest.raises(type(error)):
        runtime.ask("Pregunta ficticia")
    encoded = json.dumps(runtime.session_dict(), ensure_ascii=False, allow_nan=False)
    assert "DETALLE_RESERVADO" not in encoded
    assert "CREDENCIAL_FICTICIA_NO_REGISTRAR" not in encoded
    assert "Authorization" not in encoded and "Traceback" not in encoded
    assert runtime.session_dict()["attempts"][0]["issues"]


def test_pending_attempt_is_visible_during_call_but_metadata_never_enters_model_context(setup):
    captured = []
    client = Client([answer()])
    runtime = runtime_for(setup, client)
    client.action = lambda: captured.append(runtime.session_dict())
    runtime.ask("Pregunta")
    pending = captured[0]["attempts"][0]
    assert pending["status"] == "pending" and pending["finished_at"] is None and pending["response"] is None
    assert runtime.session_dict()["attempts"][0]["status"] == "completed"
    encoded = json.dumps(client.requests[0], ensure_ascii=False)
    assert runtime.session_id not in encoded
    assert setup.candidate.source_sha256 not in encoded
    assert runtime.session_dict()["created_at"] not in encoded


def test_requested_model_and_reported_model_are_recorded_separately(setup):
    runtime = runtime_for(setup, Client([answer()]))
    runtime.ask("Pregunta")
    snapshot = runtime.session_dict()
    assert snapshot["requested_provider"] == "ollama" and snapshot["requested_model"] == "modelo-solicitado"
    assert snapshot["attempts"][0]["response"]["model"] == "modelo-informado"


def test_summary_omits_partial_answers_and_internal_metadata(setup):
    runtime = runtime_for(setup, Client([answer("TEXTO_PARCIAL_INTERNO", finish_reason="length")]))
    with pytest.raises(LLMInvalidResponseError):
        runtime.ask("Pregunta")
    text = format_session(runtime)
    assert "TEXTO_PARCIAL_INTERNO" not in text
    assert setup.candidate.source_sha256 not in text
    assert runtime.session_dict()["instructions_text_sha256"] not in text
    assert "Preguntas enviadas: 1/20" in text and "Respuestas completas: 0" in text
    assert "Incidencias técnicas: 1" in text


def test_session_command_does_not_consume_questions_or_reset_identity_and_history(setup):
    runtime = runtime_for(setup, Client([answer()]))
    session_id = runtime.session_id
    code, text = run_entries(runtime, ["/sesion", "/iniciar", "Pregunta", "/sesion", "/iniciar", "/salir"])
    assert code == 0 and runtime.questions_asked == 1
    assert runtime.session_id == session_id and len(runtime.history_messages()) == 2
    assert f"Identificador: {session_id}" in text and "Estado: cerrada" in text
    assert runtime.session_dict()["close_reason"] == "user_exit"


@pytest.mark.parametrize("ending, reason", [(EOFError(), "end_of_input"), (KeyboardInterrupt(), "interrupted")])
def test_console_termination_without_questions_closes_with_reason(setup, ending, reason):
    runtime = runtime_for(setup, Client([]))
    code, _ = run_entries(runtime, [ending])
    assert code == 0 and runtime.session_dict()["close_reason"] == reason
    assert runtime.session_dict()["attempts"] == []


def test_console_interrupt_during_generation_finalizes_attempt_and_session(setup):
    runtime = runtime_for(setup, Client([KeyboardInterrupt()]))
    code, text = run_entries(runtime, ["/iniciar", "Pregunta"])
    snapshot = runtime.session_dict()
    assert code == 0 and snapshot["close_reason"] == "interrupted"
    assert snapshot["attempts"][0]["status"] == "interrupted"
    assert "Estado: cerrada" in text and "Incidencias técnicas: 1" in text


def test_final_integrity_check_updates_record_even_after_console_closes(setup, tmp_path, monkeypatch, capsys):
    path = tmp_path / "candidate.json"
    path.write_bytes(setup.candidate.source_path.read_bytes())
    copied_setup = load_interview_setup(candidate_path=path)
    seen = []

    class ContextClient(Client):
        provider = "ollama"

        def __init__(self):
            super().__init__([])
            self.settings = type("Settings", (), {"model": "simulado"})()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    def close_and_change(runtime, **_):
        seen.append(runtime)
        runtime.close("user_exit")
        path.write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(run_interview, "load_interview_setup", lambda: copied_setup)
    monkeypatch.setattr(run_interview, "create_client", ContextClient)
    monkeypatch.setattr(run_interview, "run_console", close_and_change)
    assert run_interview.main() == 1
    snapshot = seen[0].session_dict()
    assert snapshot["source_integrity"] == "failed"
    assert snapshot["close_reason"] == "user_exit"
    assert snapshot["issues"][0]["code"] == "profile_integrity_error"
    assert snapshot["attempts"] == []
    text = capsys.readouterr().out
    assert "Archivo original del candidato intacto" not in text
    assert "Registro de sesión guardado:" in text
    files = list(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json"))
    assert len(files) == 1
    assert session_log.load_session(files[0]) == snapshot
    with pytest.raises(ProfileIntegrityError):
        seen[0].assert_source_unchanged()
    assert len(seen[0].session_dict()["issues"]) == 1
    path.write_bytes(setup.candidate.source_path.read_bytes())
    seen[0].assert_source_unchanged()
    assert seen[0].session_dict()["source_integrity"] == "failed"

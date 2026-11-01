"""Archivos de sesiones cerradas: contratos, aislamiento y fallos de escritura."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from harness import session_log
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMInvalidResponseError, LLMResponse, LLMTimeoutError
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import SessionLogError, load_session, save_session
from harness.session_state import describe_issue


class Client:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)

    def generate(self, messages):
        result = next(self.outcomes)
        if isinstance(result, BaseException):
            raise result
        return result


def response(**changes):
    values = dict(text="Estudié Ingeniería en Informática.\nNicolás", model="modelo-local",
                  provider="ollama", elapsed_seconds=0.25, input_tokens=41, output_tokens=8,
                  finish_reason="stop", server_total_seconds=0.24, cached_input_tokens=40)
    return LLMResponse(**(values | changes))


def runtime_for(outcomes):
    return InterviewRuntime(load_interview_setup(), load_instructions(), Client(outcomes),
                            provider="ollama", model="modelo-solicitado")


@pytest.fixture
def closed_record():
    runtime = runtime_for([response()])
    runtime.ask("  ¿Dónde estudiaste?\n")
    runtime.close("user_exit")
    return runtime.session_dict()


def test_round_trip_preserves_exact_text_metrics_and_input_without_reopening(closed_record, tmp_path):
    before = deepcopy(closed_record)
    path = save_session(closed_record, tmp_path / "sesiones")
    assert path.is_absolute() and path.name == f"session-{closed_record['session_id']}.json"
    raw = path.read_bytes()
    assert "¿Dónde".encode() in raw and "Nicolás".encode() in raw
    assert not raw.startswith(b"\xef\xbb\xbf")
    loaded = load_session(path)
    assert loaded == closed_record == before
    loaded["attempts"][0]["response"]["text"] = "Cambio de la copia"
    assert load_session(path) == before and path.read_bytes() == raw


def test_empty_sessions_have_distinct_files_and_do_not_delete_previous_records(tmp_path):
    first, second = runtime_for([]), runtime_for([])
    first.close("user_exit")
    second.close("end_of_input")
    paths = [save_session(r.session_dict(), tmp_path) for r in (first, second)]
    assert paths[0] != paths[1]
    assert len(list(tmp_path.glob("session-*.json"))) == 2
    assert [load_session(p)["attempts"] for p in paths] == [[], []]


def test_duplicate_session_never_overwrites_existing_bytes(closed_record, tmp_path):
    path = save_session(closed_record, tmp_path)
    before = path.read_bytes()
    closed_record["attempts"][0]["question"] = "Otra pregunta"
    with pytest.raises(SessionLogError, match="no se sobrescribió"):
        save_session(closed_record, tmp_path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(("field_path", "value"), [
    (("session_version",), "2.0.0"),
    (("status",), "open"),
    (("closed_at",), None),
    (("close_reason",), "arbitrario"),
    (("session_id",), "../otro-archivo"),
    (("session_id",), "00000000-0000-4000-8000-00000000000g"),
    (("api_key",), "VALOR_RESERVADO"),
    (("candidate_source_sha256",), "huella-inválida"),
    (("candidate_id",), "otro-candidato"),
    (("job_id",), "otro-puesto"),
    (("configuration", "max_questions"), 0),
    (("configuration", "api_key"), "VALOR_RESERVADO"),
    (("created_at",), "2026-02-30T12:00:00+00:00"),
    (("closed_at",), "2026-10-31T12:00:00-03:00"),
    (("closed_at",), "2026-10-31"),
    (("closed_at",), "20261031T120000Z"),
    (("closed_at",), "2026-10-31T12:00:00"),
    (("close_reason",), "question_limit"),
    (("attempts", 0, "question_number"), 2),
    (("attempts", 0, "question"), "  "),
    (("attempts", 0, "status"), "pending"),
    (("attempts", 0, "response"), None),
    (("attempts", 0, "response", "finish_reason"), "length"),
    (("attempts", 0, "response", "elapsed_seconds"), -1),
    (("attempts", 0, "response", "elapsed_seconds"), float("nan")),
    (("attempts", 0, "response", "text"), "\ud800"),
    (("attempts", 0, "response", "input_tokens"), True),
    (("attempts", 0, "finished_at"), "texto"),
    (("attempts", 0, "issues"), [describe_issue(LLMTimeoutError("reservado"))]),
    (("attempts", 0, "status"), "error"),
    (("issues",), [{"recorded_at": "2026-10-31T12:00:00+00:00",
                    **describe_issue(ProfileIntegrityError(Path("reservado"), "sha256", "reservado"))}]),
])
def test_invalid_records_are_rejected_before_creating_directory(closed_record, tmp_path, field_path, value):
    target = closed_record
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = value
    directory = tmp_path / "no-creada"
    with pytest.raises(SessionLogError) as caught:
        save_session(closed_record, directory)
    assert not directory.exists()
    assert "VALOR_RESERVADO" not in str(caught.value)


def test_attempt_limit_and_consecutive_numbers_are_checked(closed_record, tmp_path):
    closed_record["configuration"]["max_questions"] = 1
    second = deepcopy(closed_record["attempts"][0])
    closed_record["attempts"].append(second)
    with pytest.raises(SessionLogError, match="límite"):
        save_session(closed_record, tmp_path / "limit")
    closed_record["configuration"]["max_questions"] = 20
    with pytest.raises(SessionLogError, match="consecutivamente"):
        save_session(closed_record, tmp_path / "number")


def test_error_partial_and_interrupted_attempts_survive_round_trip(tmp_path):
    runtime = runtime_for([LLMTimeoutError("SECRETO_TIMEOUT"), response(finish_reason="length"), KeyboardInterrupt()])
    for error in (LLMTimeoutError, LLMInvalidResponseError, KeyboardInterrupt):
        with pytest.raises(error):
            runtime.ask("Pregunta de prueba")
    runtime.close("interrupted")
    snapshot = runtime.session_dict()
    loaded = load_session(save_session(snapshot, tmp_path))
    assert loaded == snapshot
    assert [a["status"] for a in loaded["attempts"]] == ["error", "incomplete", "interrupted"]
    assert loaded["attempts"][1]["response"]["finish_reason"] == "length"
    assert "SECRETO_TIMEOUT" not in json.dumps(loaded)
    assert runtime.history_messages() == []
    loaded["attempts"][1]["response"]["finish_reason"] = "stop"
    with pytest.raises(SessionLogError, match="incompleto"):
        save_session(loaded, tmp_path / "invalid")


def test_late_integrity_issue_and_clock_adjustment_remain_valid(closed_record, tmp_path):
    closed_record["closed_at"] = "2020-01-01T00:00:00+00:00"
    closed_record["source_integrity"] = "failed"
    closed_record["issues"] = [{"recorded_at": "2026-10-31T12:00:00+00:00",
                                **describe_issue(ProfileIntegrityError(Path("privado"), "sha256", "ruta privada"))}]
    assert load_session(save_session(closed_record, tmp_path)) == closed_record


@pytest.mark.parametrize("raw", [b'{', b'{"clave":1,"clave":2}', b'{"valor":NaN}', b'[]'])
def test_loading_invalid_json_is_read_only_and_does_not_echo_content(tmp_path, raw):
    path = tmp_path / "invalid.json"
    path.write_bytes(raw)
    with pytest.raises(SessionLogError):
        load_session(path)
    assert path.read_bytes() == raw


def test_missing_file_and_missing_schema_report_safe_errors(closed_record, tmp_path, monkeypatch):
    with pytest.raises(SessionLogError, match="No se pudo leer"):
        load_session(tmp_path / "missing.json")
    monkeypatch.setattr(session_log, "SESSION_SCHEMA_PATH", tmp_path / "missing-schema.json")
    with pytest.raises(SessionLogError, match="esquemas locales"):
        save_session(closed_record, tmp_path / "not-created")
    assert not (tmp_path / "not-created").exists()


def test_file_instead_of_directory_is_preserved(closed_record, tmp_path):
    blocked = tmp_path / "carpeta"
    blocked.write_bytes(b"existente")
    with pytest.raises(SessionLogError, match="preparar la carpeta"):
        save_session(closed_record, blocked)
    assert blocked.read_bytes() == b"existente"


@pytest.mark.parametrize("error", [OSError("ERROR_RESERVADO"), KeyboardInterrupt()])
def test_failed_flush_removes_only_its_own_file(closed_record, tmp_path, monkeypatch, error):
    other = tmp_path / "existente.json"
    other.write_bytes(b"conservar")

    def fail(_):
        raise error

    monkeypatch.setattr(session_log.os, "fsync", fail)
    with pytest.raises(KeyboardInterrupt if isinstance(error, KeyboardInterrupt) else SessionLogError) as caught:
        save_session(closed_record, tmp_path)
    assert list(tmp_path.iterdir()) == [other]
    assert other.read_bytes() == b"conservar"
    assert "ERROR_RESERVADO" not in str(caught.value)

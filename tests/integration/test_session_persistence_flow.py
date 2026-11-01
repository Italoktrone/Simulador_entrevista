"""Consola, proveedor simulado y lectura de los archivos realmente guardados."""

import json
from pathlib import Path

import httpx
import pytest

from harness import session_log
from harness.llm.factory import create_client
from harness.session_log import SessionLogError, load_session
from scripts import run_interview


@pytest.mark.parametrize(("entries", "reason", "statuses"), [
    (["/salir"], "user_exit", []),
    ([EOFError()], "end_of_input", []),
    ([KeyboardInterrupt()], "interrupted", []),
    (["/iniciar", "¿Dónde estudiaste?", "/salir"], "user_exit", ["completed"]),
    (["/iniciar", "Falla", "¿Dónde estudiaste?", "/salir"], "user_exit", ["error", "completed"]),
])
def test_main_saves_closed_record_and_loader_preserves_sources(monkeypatch, capsys, entries, reason, statuses):
    root = Path(__file__).resolve().parents[2]
    paths = [root / p for p in ("data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
                               "config/interviews/basica.json", "agent/agent.md")]
    before = [p.read_bytes() for p in paths]
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if payload["messages"][-1]["content"] == "Falla":
            return httpx.Response(500, json={"error": "CUERPO_HTTP_RESERVADO"})
        assert [m["role"] for m in payload["messages"]] == ["system", "user"]
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": "Estudié Ingeniería en Informática."}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    values = iter(entries)

    def read(_):
        value = next(values)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr("builtins.input", read)
    assert run_interview.main() == 0
    text = capsys.readouterr().out
    files = list(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json"))
    assert len(files) == 1
    loaded = load_session(files[0])
    assert loaded["status"] == "closed" and loaded["close_reason"] == reason
    assert loaded["source_integrity"] == "unchanged"
    assert [a["status"] for a in loaded["attempts"]] == statuses
    assert loaded["session_id"] in text and str(files[0]) in text
    assert "Registro de sesión guardado:" in text
    assert "CUERPO_HTTP_RESERVADO" not in text + files[0].read_text(encoding="utf-8")
    assert client._http.is_closed and len(requests) == len(statuses)
    assert [p.read_bytes() for p in paths] == before


@pytest.mark.parametrize("error", [SessionLogError("No se pudo escribir"), KeyboardInterrupt()])
def test_main_reports_save_failure_without_claiming_success(monkeypatch, capsys, error):
    client = create_client({}, transport=httpx.MockTransport(lambda _: pytest.fail("No se esperaba una solicitud")))

    def fail(_):
        raise error

    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr(run_interview, "save_session", fail)
    monkeypatch.setattr("builtins.input", lambda _: "/salir")
    assert run_interview.main() == 1
    text = capsys.readouterr().out
    assert "Registro de sesión guardado:" not in text
    assert not session_log.DEFAULT_SESSIONS_DIR.exists()


def test_failure_before_creating_runtime_does_not_fabricate_session(monkeypatch, capsys):
    def fail():
        raise ValueError("Configuración no válida")

    monkeypatch.setattr(run_interview, "load_interview_setup", fail)
    assert run_interview.main() == 1
    assert not session_log.DEFAULT_SESSIONS_DIR.exists()
    assert "Registro de sesión guardado:" not in capsys.readouterr().out

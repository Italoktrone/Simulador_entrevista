"""Sesión desde la consola real con fallo HTTP y recuperación simulados."""

import json
from pathlib import Path

import httpx

from harness.application.cli import run_console
from harness.llm.factory import create_client
from scripts import run_interview


def test_entry_point_records_failed_and_complete_attempts_without_leaking_or_changing_sources(monkeypatch, capsys):
    root = Path(__file__).resolve().parents[2]
    paths = [root / p for p in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]
    before = [p.read_bytes() for p in paths]
    requests = []
    snapshots = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert [m["role"] for m in payload["messages"]] == ["system", "user"]
        if len(requests) == 1:
            return httpx.Response(500, json={"error": "CUERPO_HTTP_RESERVADO"})
        assert payload["messages"][-1]["content"] == "Segunda pregunta"
        return httpx.Response(200, json={
            "model": "gemma4:e4b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": "Respuesta completa simulada"},
        })

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    entries = iter(["/sesion", "/iniciar", "Primera pregunta", "/sesion", "Segunda pregunta", "/sesion", "/salir"])

    def observe(runtime, **kwargs):
        try:
            return run_console(runtime, **kwargs)
        finally:
            snapshots.append(runtime.session_dict())

    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr(run_interview, "run_console", observe)
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main() == 0
    text = capsys.readouterr().out
    snapshot = snapshots[0]
    assert len(requests) == 2
    assert snapshot["requested_provider"] == "ollama" and snapshot["requested_model"] == "gemma4:e4b"
    assert snapshot["status"] == "closed" and snapshot["close_reason"] == "user_exit"
    assert [a["status"] for a in snapshot["attempts"]] == ["error", "completed"]
    assert snapshot["attempts"][0]["issues"][0]["code"] == "provider_error"
    assert "CUERPO_HTTP_RESERVADO" not in text + json.dumps(snapshot, ensure_ascii=False)
    assert "Preguntas enviadas: 2/20" in text and "Respuestas completas: 1" in text
    assert "Incidencias técnicas: 1" in text and "Estado: cerrada" in text
    assert snapshot["session_id"] not in json.dumps(requests, ensure_ascii=False)
    assert client._http.is_closed
    assert json.loads(json.dumps(snapshot, ensure_ascii=False, allow_nan=False)) == snapshot
    assert [p.read_bytes() for p in paths] == before

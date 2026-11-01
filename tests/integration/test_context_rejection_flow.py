"""Un exceso se registra, conserva el historial y permite una pregunta menor."""

import json

import httpx

from harness import session_log
from harness.application.cli import run_console
from harness.llm.factory import create_client
from harness.session_log import load_session
from scripts import run_interview


def test_rejection_does_not_remove_prior_context_or_pollute_next_request_and_is_saved(monkeypatch, capsys):
    requests = []
    seen = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["truncate"] is False and payload["shift"] is False
        assert payload["model"] == "gemma4:e4b"
        messages = payload["messages"]
        if len(requests) == 2:
            assert messages[1:3] == [{"role": "user", "content": "Primer proyecto"},
                                     {"role": "assistant", "content": "Inventario Aula"}]
            return httpx.Response(400, json={"error": json.dumps({"error": {
                "type": "exceed_context_size_error", "message": "DETALLE_RESERVADO", "code": 400,
            }})})
        if len(requests) == 3:
            assert messages[1:] == [
                {"role": "user", "content": "Primer proyecto"},
                {"role": "assistant", "content": "Inventario Aula"},
                {"role": "user", "content": "¿Cómo se llamaba?"},
            ]
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": "Inventario Aula"}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    entries = iter(["/iniciar", "Primer proyecto", "PREGUNTA_EXTENSA", "¿Cómo se llamaba?", "/salir"])

    def observe(runtime, **kwargs):
        seen.append(runtime)
        return run_console(runtime, **kwargs)

    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr(run_interview, "run_console", observe)
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main() == 0
    text = capsys.readouterr().out
    files = list(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json"))
    assert len(files) == 1 and len(requests) == 3 and client._http.is_closed
    record = load_session(files[0])
    assert record == seen[0].session_dict()
    assert [a["status"] for a in record["attempts"]] == ["completed", "error", "completed"]
    failed = record["attempts"][1]
    assert failed["response"] is None and failed["issues"][0]["code"] == "context_limit"
    assert record["source_integrity"] == "unchanged" and record["close_reason"] == "user_exit"
    assert "Preguntas enviadas: 3/20" in text and "Respuestas completas: 2" in text
    assert "falta de espacio de contexto" in text and "DETALLE_RESERVADO" not in text + json.dumps(record)
    assert requests[0]["messages"][0] == requests[2]["messages"][0]

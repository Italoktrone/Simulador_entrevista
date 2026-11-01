"""Consola con resumen optativo y proveedor HTTP simulado, sin datos reescritos."""

import json

import httpx
import pytest

from harness import session_log
from harness.history_summary import SELECTION_INSTRUCTIONS
from harness.llm.factory import create_client
from harness.session_log import load_session
from scripts import run_interview


@pytest.mark.parametrize("selector_result", ["valid", "invalid", "interrupted"])
def test_console_policy_records_selections_separately_and_saves_new_format(monkeypatch, capsys, selector_result):
    candidates = 0
    selections = 0

    def handler(request):
        nonlocal candidates, selections
        payload = json.loads(request.content)
        assert payload["truncate"] is False and payload["shift"] is False
        if payload["messages"][0]["content"] == SELECTION_INSTRUCTIONS:
            selections += 1
            if selector_result == "interrupted":
                raise KeyboardInterrupt()
            source = json.loads(payload["messages"][1]["content"])
            text = json.dumps({"selections": [{"question_number": t["question_number"], "segment_indices": t["required_segment_indices"]} for t in source["old_turns"]]}) if selector_result == "valid" else "TEXTO_RESERVADO"
        else:
            candidates += 1
            text = "Inventario Aula fue académico sin clientes comerciales."
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop", "message": {"role": "assistant", "content": text}, "prompt_eval_count": 6100})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    entries = iter(["/iniciar", "Primera", "Segunda", "Tercera", "Cuarta", "/salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main(["--extractive-context", "--summary-trigger-tokens", "1"]) == 0
    output = capsys.readouterr().out
    files = list(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json"))
    assert len(files) == 1 and client._http.is_closed
    record = load_session(files[0])
    assert record["session_version"] == "1.1.0" and len(record["context_events"]) == 4
    assert selections == 1 and candidates == (3 if selector_result == "interrupted" else 4)
    assert len(record["attempts"]) == candidates
    assert "TEXTO_RESERVADO" not in output + json.dumps(record)
    last = record["context_events"][-1]
    assert last["selector_status"] == {"valid": "completed", "invalid": "failed", "interrupted": "interrupted"}[selector_result]
    assert last["candidate_sent"] is (selector_result != "interrupted")
    assert "Selecciones de memoria: 1" in output and "Archivo original del candidato intacto." in output


def test_invalid_policy_never_sends_http_or_creates_session(monkeypatch, capsys):
    client = create_client({}, transport=httpx.MockTransport(lambda _: pytest.fail("No debe enviar")))
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    assert run_interview.main(["--extractive-context", "--summary-trigger-tokens", "9000"]) == 1
    assert not session_log.DEFAULT_SESSIONS_DIR.exists() and client._http.is_closed
    assert "No se pudo iniciar" in capsys.readouterr().out

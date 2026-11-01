"""Escenario real, resumen, contexto y proveedor simulado, conservando archivos."""

import json

import httpx
import pytest

from harness.history_summary import SELECTION_INSTRUCTIONS
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse
from harness.llm.factory import create_client
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import save_session
from harness.summary_context import EXTRACT_GUIDANCE, EXTRACT_MARKER
from scripts import probe_summary_context


def archive(tmp_path, long=True):
    filler = "Esta explicación general introduce el tema de la conversación y desarrolla una presentación extensa de la respuesta. " * (12 if long else 0)
    values = iter(["Elegí Inventario Aula. " + filler + "Fue académico sin clientes comerciales.", "Utilicé pytest."])

    class Client:
        def generate(self, messages):
            return LLMResponse(next(values), "fixture", "simulado", 0.0, finish_reason="stop")

    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), Client())
    runtime.ask("Primer proyecto")
    runtime.ask("Última herramienta")
    runtime.close("user_exit")
    return save_session(runtime.session_dict(), tmp_path)


@pytest.mark.parametrize("long", [True, False])
def test_probe_composes_then_queries_and_never_changes_archived_session(tmp_path, monkeypatch, capsys, long):
    path = archive(tmp_path, long)
    before = path.read_bytes()
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["truncate"] is False and payload["shift"] is False
        if payload["messages"][0]["content"] == SELECTION_INSTRUCTIONS:
            source = json.loads(payload["messages"][1]["content"])
            content = json.dumps({"selections": [{"question_number": t["question_number"], "segment_indices": t["required_segment_indices"]} for t in source["old_turns"]]})
        else:
            messages = payload["messages"]
            assert [m["role"] for m in messages] == ["system", "user", "assistant", "user", "assistant", "user"]
            assert messages[-1]["content"] == "¿Cuál mencioné primero?"
            assert messages[-3:-1] == [{"role": "user", "content": "Última herramienta"}, {"role": "assistant", "content": "Utilicé pytest."}]
            assert "candidate_profile" in messages[0]["content"]
            assert messages[0]["content"].endswith(EXTRACT_GUIDANCE) if long else EXTRACT_GUIDANCE not in messages[0]["content"]
            assert messages[2]["content"].startswith(EXTRACT_MARKER) if long else messages[2]["content"] == "Elegí Inventario Aula. Fue académico sin clientes comerciales."
            content = "Mencioné primero Inventario Aula."
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop", "message": {"role": "assistant", "content": content}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(probe_summary_context, "create_client", lambda: client)
    assert probe_summary_context.main([str(path), "--keep-recent-pairs", "1", "--question", "¿Cuál mencioné primero?"]) == 0
    output = capsys.readouterr().out
    assert "Contexto elegido: resumen extractivo" in output if long else "Contexto elegido: historial completo" in output
    assert "Respuesta de comprobación: Mencioné primero Inventario Aula." in output
    assert len(requests) == 2 and client._http.is_closed
    assert path.read_bytes() == before and len(list(tmp_path.glob("session-*.json"))) == 1


@pytest.mark.parametrize("outcome", ["length", "provider_error", "interrupt"])
def test_probe_does_not_claim_success_on_incomplete_or_failed_candidate(tmp_path, monkeypatch, capsys, outcome):
    path = archive(tmp_path, long=False)
    before = path.read_bytes()

    def handler(request):
        if outcome == "interrupt":
            raise KeyboardInterrupt()
        if outcome == "provider_error":
            return httpx.Response(500, json={"error": "DETALLE_RESERVADO"})
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "length", "message": {"role": "assistant", "content": "RESPUESTA_PARCIAL"}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(probe_summary_context, "create_client", lambda: client)
    assert probe_summary_context.main([str(path), "--keep-recent-pairs", "20", "--question", "Pregunta"]) == 1
    output = capsys.readouterr().out
    assert "Respuesta de comprobación:" not in output
    assert "RESPUESTA_PARCIAL" not in output and "DETALLE_RESERVADO" not in output
    assert path.read_bytes() == before and client._http.is_closed


def test_mismatched_instructions_fail_before_creating_client(tmp_path, monkeypatch, capsys):
    path = archive(tmp_path, long=False)
    monkeypatch.setattr(probe_summary_context, "load_instructions", lambda: load_instructions() + "\nCambio de reglas")
    monkeypatch.setattr(probe_summary_context, "create_client", lambda: pytest.fail("No debe gastar una llamada"))
    assert probe_summary_context.main([str(path), "--question", "Pregunta"]) == 1
    assert "no corresponden" in capsys.readouterr().out

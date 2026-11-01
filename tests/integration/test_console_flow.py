"""Consola completa con datos y adaptador reales, proveedor HTTP simulado."""

import json
from pathlib import Path

import httpx

from harness.llm.factory import create_client
from scripts import run_interview


def test_console_entry_point_uses_real_setup_and_adapter_without_changing_sources(monkeypatch, capsys):
    root = Path(__file__).resolve().parents[2]
    sources = [root / relative for relative in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]
    original = {path: path.read_bytes() for path in sources}
    questions = ["¿Dónde estudiaste?", "¿Has trabajado con Kubernetes?"]
    entries = iter(["/cv", "/puesto", "/iniciar", *questions, "/salir"])
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 1:
            assert payload["messages"][0]["content"].endswith(
                "\n\nPREGUNTA_DEL_ENTREVISTADOR (entrada de conversación):\n" + questions[0]
            )
            assert [item["role"] for item in payload["messages"]] == ["user"]
        else:
            assert [item["role"] for item in payload["messages"]] == ["user", "assistant", "user"]
            assert payload["messages"][1:] == [
                {"role": "assistant", "content": "Respuesta simulada 1."},
                {"role": "user", "content": questions[1]},
            ]
        return httpx.Response(200, json={
            "model": "gemma3n:e2b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": f"Respuesta simulada {len(requests)}."},
        })

    client = create_client({}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main() == 0
    output = capsys.readouterr().out
    assert len(requests) == 2
    marker = "\n\nPREGUNTA_DEL_ENTREVISTADOR (entrada de conversación):\n"
    assert requests[0]["messages"][0]["content"].split(marker, 1)[0] == (
        requests[1]["messages"][0]["content"].split(marker, 1)[0]
    )
    assert questions[0] in requests[1]["messages"][0]["content"]
    assert "CURRÍCULUM RESUMIDO" in output and "COMPETENCIAS A EXPLORAR" in output
    assert "Candidato: Respuesta simulada 1." in output and "Candidato: Respuesta simulada 2." in output
    assert "Archivo original del candidato intacto" in output
    assert client._http.is_closed
    assert {path: path.read_bytes() for path in sources} == original

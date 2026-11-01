"""Escenario aprobado y adaptador opcional con API simulada, sin red."""

import json
from pathlib import Path

import httpx

from harness.interview_config import load_interview_setup
from harness.llm.factory import create_client
from harness.prompt_builder import build_messages, load_instructions


def test_external_initial_turn_preserves_context_and_source_files():
    root = Path(__file__).resolve().parents[2]
    sources = [root / relative for relative in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]
    original = {path: path.read_bytes() for path in sources}
    setup = load_interview_setup()
    messages = build_messages(setup, "¿Dónde estudiaste?", instructions=load_instructions())
    key = "clave-ficticia-solo-pruebas"

    def handler(request):
        payload = json.loads(request.content)
        assert payload["input"] == messages
        assert payload["store"] is False
        assert key not in request.content.decode("utf-8")
        assert "Instituto Profesional Horizonte Digital" in payload["input"][0]["content"]
        return httpx.Response(200, json={
            "model": "modelo-ficticio-001", "status": "completed",
            "output": [{"type": "message", "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": "Respuesta de integración simulada."}]}],
            "usage": {"input_tokens": 50, "output_tokens": 8},
        })

    with create_client({
        "LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true",
        "OPENAI_MODEL": "modelo-ficticio-001", "OPENAI_API_KEY": key,
    }, transport=httpx.MockTransport(handler)) as client:
        response = client.generate(messages)
    assert response.provider == "openai"
    assert response.text == "Respuesta de integración simulada."
    setup.candidate.assert_source_unchanged()
    assert {path: path.read_bytes() for path in sources} == original

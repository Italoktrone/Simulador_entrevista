"""Recorrido de datos reales a una respuesta HTTP simulada, sin red."""

import json
from pathlib import Path

import httpx

from harness.interview_config import load_interview_setup
from harness.llm.ollama_client import OllamaClient
from harness.prompt_builder import build_messages, load_instructions


def test_initial_turn_with_local_adapter_preserves_originals():
    root = Path(__file__).resolve().parents[2]
    sources = [root / relative for relative in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]
    original = {path: path.read_bytes() for path in sources}
    setup = load_interview_setup()
    question = "¿Dónde estudiaste?"
    messages = build_messages(setup, question, instructions=load_instructions())

    def handler(request):
        payload = json.loads(request.content)
        assert [message["role"] for message in payload["messages"]] == ["user"]
        assert payload["messages"][0]["content"] == (
            messages[0]["content"]
            + "\n\nPREGUNTA_DEL_ENTREVISTADOR (entrada de conversación):\n" + question
        )
        assert messages[1] == {"role": "user", "content": question}
        assert setup.candidate.to_dict()["name"] in payload["messages"][0]["content"]
        return httpx.Response(200, json={
            "model": "gemma3n:e2b", "message": {"role": "assistant", "content": "Respuesta simulada."},
            "done": True, "done_reason": "stop",
        })

    with OllamaClient(transport=httpx.MockTransport(handler)) as client:
        assert client.generate(messages).text == "Respuesta simulada."
    setup.candidate.assert_source_unchanged()
    assert {path: path.read_bytes() for path in sources} == original

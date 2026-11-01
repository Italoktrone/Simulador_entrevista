"""Flujo de historial con escenario real y Gemma 4 mediante HTTP simulado."""

import json

import httpx

from harness.interview_config import load_interview_setup
from harness.llm.factory import create_client
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime


def test_followup_and_new_interview_use_separate_contexts_with_native_roles():
    setup = load_interview_setup()
    source_before = setup.candidate.source_path.read_bytes()
    requests = []
    first_answer = "Mi proyecto académico fue Inventario Aula; aporté al backend de productos y movimientos."

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        messages = payload["messages"]
        assert payload["model"] == "gemma4:e4b" and request.url.host == "127.0.0.1"
        if len(requests) == 2:
            assert [message["role"] for message in messages] == ["system", "user", "assistant", "user"]
            assert messages[1:] == [
                {"role": "user", "content": "Cuéntame de tu proyecto académico."},
                {"role": "assistant", "content": first_answer},
                {"role": "user", "content": "¿Ese proyecto llegó a producción?"},
            ]
            text = "No tuvo operación real en producción."
        else:
            assert [message["role"] for message in messages] == ["system", "user"]
            text = first_answer
        return httpx.Response(200, json={
            "model": "gemma4:e4b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": text},
        })

    with create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler)) as client:
        runtime = InterviewRuntime(setup, load_instructions(), client)
        runtime.ask("Cuéntame de tu proyecto académico.")
        runtime.ask("¿Ese proyecto llegó a producción?")
        runtime.close()
        assert len(runtime.history_messages()) == 4
        another = InterviewRuntime(setup, load_instructions(), client)
        another.ask("Primera pregunta de otra entrevista.")
        assert len(another.history_messages()) == 2
    assert len(requests) == 3 and client._http.is_closed
    assert source_before == setup.candidate.source_path.read_bytes()
    setup.candidate.assert_source_unchanged()

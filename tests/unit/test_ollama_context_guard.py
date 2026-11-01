"""Rechazo explícito de contexto, sin recortes, reintentos ni cuerpos en el error."""

from copy import deepcopy
import json

import httpx
import pytest

from harness.llm.client import LLMContextLimitError, LLMProviderError
from harness.llm.config import OllamaSettings
from harness.llm.ollama_client import OllamaClient
from harness.session_state import describe_issue


ENGINE_ERROR = {"error": {"type": "exceed_context_size_error", "message": "DETALLE_RESERVADO", "code": 400}}
MESSAGES = [
    {"role": "system", "content": "Reglas fijas"},
    {"role": "user", "content": "Primera pregunta"},
    {"role": "assistant", "content": "Primera respuesta"},
    {"role": "user", "content": "Segunda pregunta"},
]


@pytest.mark.parametrize("model", ["gemma3n:e2b", "gemma4:e4b"])
def test_every_local_request_disables_truncation_and_shift_without_changing_messages(model):
    before = deepcopy(MESSAGES)
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["truncate"] is False and payload["shift"] is False
        assert "truncate" not in payload["options"] and "shift" not in payload["options"]
        assert payload["options"]["num_ctx"] == 8192 and payload["options"]["num_predict"] == 512
        assert payload["messages"][-2:] == MESSAGES[-2:]
        return httpx.Response(200, json={"model": model, "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": "Respuesta completa"}})

    with OllamaClient(OllamaSettings(model=model), transport=httpx.MockTransport(handler)) as client:
        assert client.generate(MESSAGES).text == "Respuesta completa"
    assert MESSAGES == before and len(requests) == 1


@pytest.mark.parametrize("body", [
    ENGINE_ERROR,
    {"error": json.dumps(ENGINE_ERROR)},
    {"error": "the input length exceeds the context length"},
    {"error": "request (16009 tokens) exceeds the available context size (8192 tokens), try increasing it"},
])
@pytest.mark.parametrize("status", [400, 200])
def test_known_context_rejections_are_safe_and_never_retried(body, status):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json=body)

    settings = OllamaSettings(model="gemma4:e4b")
    with OllamaClient(settings, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMContextLimitError) as caught:
            client.generate(MESSAGES)
        assert client.settings is settings
    assert len(requests) == 1
    assert "DETALLE_RESERVADO" not in str(caught.value)
    assert "contexto" in str(caught.value) and "No se repitió" in str(caught.value)
    assert describe_issue(caught.value)["code"] == "context_limit"


@pytest.mark.parametrize("body", [
    {"error": "otro error de contexto DETALLE_RESERVADO"},
    {"error": "{JSON roto DETALLE_RESERVADO"},
    {"error": json.dumps({"error": "otro error"})},
    {"error": {"type": "otro_error", "message": "DETALLE_RESERVADO"}},
    {"error": ["exceed_context_size_error"]},
    [],
])
def test_other_bad_requests_keep_generic_error_and_do_not_echo_body(body):
    with OllamaClient(transport=httpx.MockTransport(lambda _: httpx.Response(400, json=body))) as client:
        with pytest.raises(LLMProviderError) as caught:
            client.generate(MESSAGES)
    assert "DETALLE_RESERVADO" not in str(caught.value)


def test_context_catalogue_does_not_copy_arbitrary_error_text():
    issue = describe_issue(LLMContextLimitError("CREDENCIAL_RESERVADA"))
    assert issue["code"] == "context_limit" and issue["error_type"] == "LLMContextLimitError"
    assert "CREDENCIAL_RESERVADA" not in str(issue)

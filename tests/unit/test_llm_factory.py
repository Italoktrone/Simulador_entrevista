"""La clave no activa la API; la selección y el permiso son explícitos."""

import json

import httpx
import pytest

from harness.llm.client import LLMConnectionError
from harness.llm.config import LLMConfigurationError
from harness.llm.factory import create_client
from harness.llm.ollama_client import OllamaClient
from harness.llm.openai_client import OpenAIClient


EXTERNAL = {
    "LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true",
    "OPENAI_MODEL": "modelo-ficticio-001", "OPENAI_API_KEY": "clave-ficticia-solo-pruebas",
}


def test_default_is_local_and_creation_does_not_send_requests():
    calls = []
    with create_client({}, transport=httpx.MockTransport(lambda request: calls.append(request))) as client:
        assert isinstance(client, OllamaClient)
        assert client.settings.model == "gemma3n:e2b"
    assert calls == []


@pytest.mark.parametrize("model", ["gemma4:e2b", "gemma4:e4b"])
def test_explicit_local_model_reaches_only_local_service(model):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        payload = json.loads(request.content)
        assert payload["model"] == model
        assert payload["messages"] == [{"role": "user", "content": "Pregunta"}]
        return httpx.Response(200, json={
            "model": model, "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": "Respuesta simulada"},
        })

    with create_client({"OLLAMA_MODEL": model}, transport=httpx.MockTransport(handler)) as client:
        assert client.generate([{"role": "user", "content": "Pregunta"}]).model == model
    assert len(calls) == 1


@pytest.mark.parametrize("model", ["", "gemma4:31b-cloud"])
def test_invalid_local_selection_fails_before_requests(model):
    with pytest.raises(LLMConfigurationError, match="OLLAMA_MODEL"):
        create_client({"OLLAMA_MODEL": model}, transport=httpx.MockTransport(lambda _: pytest.fail("Sin red")))


def test_local_selection_does_not_even_read_external_credentials(monkeypatch):
    class LocalValues(dict):
        def get(self, key, default=None):
            if key.startswith("OPENAI_") or key == "LLM_ALLOW_EXTERNAL_API":
                pytest.fail("La ruta local no debe consultar la configuración externa.")
            return super().get(key, default)

    with create_client(LocalValues(LLM_PROVIDER="ollama"), transport=httpx.MockTransport(lambda _: None)) as client:
        assert client.provider == "ollama"
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_ALLOW_EXTERNAL_API", "true")
    monkeypatch.setenv("OPENAI_API_KEY", EXTERNAL["OPENAI_API_KEY"])
    with create_client(transport=httpx.MockTransport(lambda _: None)) as client:
        assert client.provider == "ollama"


@pytest.mark.parametrize("flag", [None, "false", "1", "TRUE"])
def test_external_selection_is_blocked_without_exact_explicit_permission(flag):
    values = EXTERNAL.copy()
    if flag is None:
        values.pop("LLM_ALLOW_EXTERNAL_API")
    else:
        values["LLM_ALLOW_EXTERNAL_API"] = flag
    with pytest.raises(LLMConfigurationError, match="desactivada"):
        create_client(values)


@pytest.mark.parametrize("provider", ["", "otro", "OPENAI"])
def test_unknown_provider_does_not_silently_fall_back(provider):
    with pytest.raises(LLMConfigurationError, match="LLM_PROVIDER"):
        create_client(EXTERNAL | {"LLM_PROVIDER": provider})


@pytest.mark.parametrize("field", ["OPENAI_MODEL", "OPENAI_API_KEY"])
def test_enabled_external_mode_requires_model_and_key(field):
    with pytest.raises(LLMConfigurationError, match=field):
        create_client({key: value for key, value in EXTERNAL.items() if key != field})


def test_explicit_external_selection_uses_only_official_endpoint():
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert json.loads(request.content)["model"] == EXTERNAL["OPENAI_MODEL"]
        return httpx.Response(200, json={
            "model": EXTERNAL["OPENAI_MODEL"], "status": "completed",
            "output": [{"type": "message", "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": "Respuesta simulada."}]}],
        })

    values = EXTERNAL | {"OPENAI_BASE_URL": "https://example.com", "HTTP_PROXY": "https://example.com"}
    with create_client(values, transport=httpx.MockTransport(handler)) as client:
        assert isinstance(client, OpenAIClient)
        assert calls == []
        assert client.generate([{"role": "user", "content": "Pregunta"}]).provider == "openai"
    assert len(calls) == 1


def test_local_connection_failure_never_calls_external_provider():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.host == "127.0.0.1"
        assert "authorization" not in request.headers
        raise httpx.ConnectError("fallo local simulado", request=request)

    with create_client(EXTERNAL | {"LLM_PROVIDER": "ollama"}, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMConnectionError):
            client.generate([{"role": "user", "content": "Pregunta"}])
    assert len(calls) == 2

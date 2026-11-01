"""Contrato de Responses con transporte simulado y credenciales ficticias."""

from copy import deepcopy
from dataclasses import asdict
import json
import traceback

import httpx
import pytest

from harness.llm.client import (
    LLMAuthenticationError, LLMConnectionError, LLMInvalidResponseError,
    LLMModelNotFoundError, LLMProviderError, LLMTimeoutError,
)
from harness.llm.config import LLMConfigurationError, OpenAISettings
from harness.llm.openai_client import OpenAIClient


KEY = "clave-ficticia-solo-pruebas"
MODEL = "modelo-ficticio-001"
MESSAGES = [{"role": "system", "content": "Reglas"}, {"role": "user", "content": "Pregunta"}]


def output_message(**changes):
    message = {
        "type": "message", "role": "assistant", "status": "completed",
        "content": [{"type": "output_text", "text": "Respuesta simulada."}],
    }
    message.update(changes)
    return message


def reply(**changes):
    data = {
        "object": "response", "model": MODEL, "status": "completed", "error": None,
        "output": [output_message()], "usage": {"input_tokens": 50, "output_tokens": 8},
    }
    data.update(changes)
    return data


def client_for(handler):
    return OpenAIClient(OpenAISettings(model=MODEL), api_key=KEY, transport=httpx.MockTransport(handler))


def test_http_contract_and_separation_of_text_from_reasoning():
    original = deepcopy(MESSAGES)

    def handler(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.method == "POST"
        assert request.headers["authorization"] == f"Bearer {KEY}"
        assert json.loads(request.content) == {
            "model": MODEL, "input": original, "max_output_tokens": 512, "store": False, "stream": False,
        }
        assert KEY not in request.content.decode()
        assert request.extensions["timeout"] == {"connect": 5.0, "read": 90.0, "write": 10.0, "pool": 5.0}
        return httpx.Response(200, json=reply(output=[
            {"type": "reasoning", "summary": [{"type": "summary_text", "text": "contenido reservado"}]},
            output_message(content=[
                {"type": "output_text", "text": "Primera parte."},
                {"type": "output_text", "text": "Segunda parte."},
            ]),
        ]))

    with client_for(handler) as client:
        assert KEY not in repr(client) + repr(client.settings) + json.dumps(asdict(client.settings))
        result = client.generate(MESSAGES)
    assert result.text == "Primera parte.\nSegunda parte."
    assert (result.model, result.provider, result.finish_reason) == (MODEL, "openai", "completed")
    assert (result.input_tokens, result.output_tokens) == (50, 8)
    assert result.elapsed_seconds >= 0
    assert MESSAGES == original


@pytest.mark.parametrize("data", [
    [], reply(status="incomplete", incomplete_details={"reason": "max_output_tokens"}),
    reply(status="failed"), reply(model=None), reply(output=None), reply(output=[]),
    reply(output=[{"type": "reasoning", "summary": []}]), reply(output=[7]),
    reply(output=[output_message(role="user")]), reply(output=[output_message(status="incomplete")]),
    reply(output=[output_message(content="texto")]),
    reply(output=[output_message(content=[{"type": "output_text", "text": " "}])]),
    reply(output=[output_message(content=[{"type": "output_text", "text": 42}])]),
    reply(output=[output_message(content=[{"type": "refusal", "refusal": "rechazo simulado"}])]),
    reply(output=[{"type": "function_call", "name": "accion_no_solicitada"}]),
    reply(output=[output_message(content=[{"type": "output_text", "text": "<think>texto</think>"}])]),
])
def test_invalid_or_incomplete_responses_are_not_candidate_answers(data):
    with client_for(lambda _: httpx.Response(200, json=data)) as client:
        with pytest.raises(LLMInvalidResponseError):
            client.generate(MESSAGES)


def test_malformed_json_is_reported_without_exposing_body():
    with client_for(lambda _: httpx.Response(200, text="{ " + KEY)) as client:
        with pytest.raises(LLMInvalidResponseError) as captured:
            client.generate(MESSAGES)
    assert KEY not in "".join(traceback.format_exception(captured.value))


def test_provider_error_in_successful_http_response_is_not_accepted():
    with client_for(lambda _: httpx.Response(200, json=reply(error={"message": KEY}))) as client:
        with pytest.raises(LLMProviderError) as captured:
            client.generate(MESSAGES)
    assert KEY not in str(captured.value)


@pytest.mark.parametrize("status, exception", [
    (307, LLMProviderError), (400, LLMProviderError), (401, LLMAuthenticationError),
    (403, LLMAuthenticationError), (404, LLMModelNotFoundError), (429, LLMProviderError),
    (500, LLMProviderError), (503, LLMProviderError),
])
def test_http_errors_are_not_retried_or_redirected_and_do_not_expose_body(status, exception):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": KEY}}, headers={"location": "https://example.com"})

    with client_for(handler) as client:
        with pytest.raises(exception) as captured:
            client.generate(MESSAGES)
    assert len(calls) == 1
    assert calls[0].url.host == "api.openai.com"
    assert KEY not in "".join(traceback.format_exception(captured.value))


@pytest.mark.parametrize("failure, expected, attempts", [
    (httpx.ConnectError, LLMConnectionError, 2), (httpx.ConnectTimeout, LLMTimeoutError, 2),
    (httpx.ReadTimeout, LLMTimeoutError, 1), (httpx.ReadError, LLMConnectionError, 1),
])
def test_network_failures_have_bounded_retries_and_hide_original_error(failure, expected, attempts):
    calls = []

    def handler(request):
        calls.append(request)
        raise failure("error simulado con " + KEY, request=request)

    with client_for(handler) as client:
        with pytest.raises(expected) as captured:
            client.generate(MESSAGES)
    assert len(calls) == attempts
    assert KEY not in "".join(traceback.format_exception(captured.value))


def test_second_connection_can_succeed_without_modifying_messages():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ConnectError("fallo simulado", request=request)
        return httpx.Response(200, json=reply())

    with client_for(handler) as client:
        assert client.generate(MESSAGES).text == "Respuesta simulada."
    assert len(calls) == 2 and calls[0].content == calls[1].content


def test_invalid_usage_is_not_invented():
    with client_for(lambda _: httpx.Response(200, json=reply(usage={"input_tokens": True, "output_tokens": -1}))) as client:
        result = client.generate(MESSAGES)
    assert result.input_tokens is None and result.output_tokens is None


@pytest.mark.parametrize("messages", [[], [{"role": "tool", "content": "texto"}]])
def test_invalid_messages_fail_before_http(messages):
    def handler(_):
        pytest.fail("No debe enviarse una solicitud inválida.")

    with client_for(handler) as client:
        with pytest.raises(ValueError):
            client.generate(messages)


@pytest.mark.parametrize("key", ["", None, "clave con espacios", "clave\n", "contraseña"])
def test_invalid_credentials_fail_without_echoing_their_value(key):
    with pytest.raises(LLMConfigurationError):
        OpenAIClient(OpenAISettings(model=MODEL), api_key=key)


@pytest.mark.parametrize("changes", [
    {"model": ""}, {"model": "con espacios"}, {"model": None},
    {"max_output_tokens": True}, {"max_output_tokens": 15},
    {"read_timeout_seconds": float("inf")}, {"connect_timeout_seconds": 0}, {"connection_retries": 3},
])
def test_invalid_external_settings_are_rejected(changes):
    with pytest.raises(LLMConfigurationError):
        OpenAISettings(**({"model": MODEL} | changes))

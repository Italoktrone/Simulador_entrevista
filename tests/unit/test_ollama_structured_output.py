"""Format nativo solo para clasificación local, con contratos y presupuestos conservados."""

from copy import deepcopy
import json

import httpx
import pytest

from harness.llm_classification_contract import classification_generation_schema
from harness.llm.config import LLMConfigurationError
from harness.llm.factory import create_client
from harness.llm.ollama_client import OllamaClient
from harness.llm_question_classifier import (
    ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)


MESSAGES = [{"role": "system", "content": "Instrucciones"}, {"role": "user", "content": "Pregunta"}]
LOCAL = {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "gemma4:e4b"}


def reply(text="Respuesta simulada."):
    return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                   "message": {"role": "assistant", "content": text}})


def test_classifier_sends_approved_strict_schema_and_candidate_keeps_free_text_budget():
    candidate_calls, classifier_calls = [], []
    def handler(calls):
        def send(request):
            calls.append(json.loads(request.content))
            return reply()
        return send
    with create_client(LOCAL, transport=httpx.MockTransport(handler(candidate_calls))) as candidate:
        with create_classification_client(LOCAL, transport=httpx.MockTransport(handler(classifier_calls))) as classifier:
            candidate.generate(MESSAGES)
            classifier.generate(MESSAGES)
    assert "format" not in candidate_calls[0]
    assert candidate_calls[0]["options"]["num_predict"] == 512
    assert classifier_calls[0]["options"]["num_predict"] == 2048
    schema = classifier_calls[0]["format"]
    assert schema == classification_generation_schema()
    assert all(branch["additionalProperties"] is False for branch in schema["oneOf"])
    assert schema["$defs"]["classification"]["additionalProperties"] is False
    assert schema["$defs"]["unit"]["additionalProperties"] is False
    assert all(field not in branch["properties"] for branch in schema["oneOf"]
               for field in ("method", "rule_ids", "technical_error", "validation_status"))


def test_schema_snapshot_cannot_be_mutated_by_caller_or_previous_request():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"], "additionalProperties": False}
    expected = deepcopy(schema)
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(deepcopy(payload["format"]))
        payload["format"]["required"].clear()
        return reply()
    with OllamaClient(output_schema=schema, transport=httpx.MockTransport(handler)) as client:
        schema["required"].clear()
        schema["properties"]["name"]["type"] = "integer"
        client.generate(MESSAGES)
        client.generate(MESSAGES)
    assert calls == [expected, expected]


@pytest.mark.parametrize("schema", [[], True, "json", {"type": "tipo_inexistente"}, {"enum": [float("nan")]}])
def test_invalid_schema_is_rejected_before_client_or_request(schema):
    with pytest.raises(ValueError, match="output_schema"):
        OllamaClient(output_schema=schema, transport=httpx.MockTransport(lambda _: pytest.fail("No debe enviar")))


@pytest.mark.parametrize("provider", ["unab", "openai"])
def test_local_format_option_cannot_be_silently_sent_to_other_providers(provider):
    with pytest.raises(LLMConfigurationError, match="solo.*Ollama"):
        create_client({"LLM_PROVIDER": provider}, output_schema={"type": "object"})


def test_explicit_prompt_mode_supports_comparison_without_changing_output_budget():
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return reply()
    with create_classification_client(LOCAL, structured_output=False,
            settings=ClassificationLLMSettings(max_output_tokens=2048), transport=httpx.MockTransport(handler)) as client:
        client.generate(MESSAGES)
    assert "format" not in calls[0]
    assert calls[0]["options"]["num_predict"] == 2048


@pytest.mark.parametrize("value", [None, 0, 1, "true"])
def test_structured_output_requires_an_explicit_boolean(value):
    with pytest.raises(ValueError, match="booleano"):
        create_classification_client(LOCAL, structured_output=value)


def test_native_format_does_not_bypass_host_validation_or_add_retries():
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return reply("NO_JSON_NO_REENVIAR")
    with create_classification_client(LOCAL, transport=httpx.MockTransport(handler)) as client:
        report = LLMQuestionClassifier(client).classify("¿Qué es SQL?", intervention_id="schema-test")
    assert report.result["technical_error"] == "json_invalido"
    assert len(calls) == 2
    assert calls[0]["format"] == calls[1]["format"] == classification_generation_schema(allowed_context_turn_ids=())
    assert "NO_JSON_NO_REENVIAR" not in json.dumps(calls[1])
    assert all(c["options"]["num_predict"] == 2048 for c in calls)


def test_request_schema_override_never_changes_client_default_or_next_request():
    default = {"type": "object", "properties": {"default": {"type": "boolean"}}}
    override = {"type": "object", "properties": {"id": {"enum": [2, 3]}}}
    expected = deepcopy(override)
    calls = []
    def handler(request):
        calls.append(json.loads(request.content)["format"])
        override["properties"].clear()
        return reply()
    with OllamaClient(output_schema=default, transport=httpx.MockTransport(handler)) as client:
        client.generate(MESSAGES, output_schema=override)
        client.generate(MESSAGES)
    assert calls == [expected, default]


@pytest.mark.parametrize("schema", [[], {"type": "wrong"}, {"enum": [float("nan")]}])
def test_bad_request_override_sends_nothing_and_keeps_default(schema):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content)["format"])
        return reply()
    with OllamaClient(output_schema={"type":"object"}, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="output_schema"):
            client.generate(MESSAGES, output_schema=schema)
        client.generate(MESSAGES)
    assert calls == [{"type":"object"}]

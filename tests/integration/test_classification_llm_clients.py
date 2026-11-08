"""Clasificador sobre adaptadores reales con HTTP simulado; nunca red real."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
import json

import httpx
import pytest

from harness.llm.config import LLMConfigurationError
from harness.llm.factory import create_client
from harness.llm_question_classifier import (
    ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)
from harness.llm_classification_contract import classification_generation_schema


ENVIRONMENTS = [
    {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "gemma4:e4b"},
    {"LLM_PROVIDER": "unab", "LLM_ALLOW_EXTERNAL_API": "true", "UNAB_MODEL": "gemma4:26b",
     "UNAB_API_KEY": "clave-ficticia-solo-pruebas", "UNAB_MAX_OUTPUT_TOKENS": "2048"},
    {"LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true", "OPENAI_MODEL": "modelo-candidato",
     "OPENAI_API_KEY": "clave-ficticia-solo-pruebas"},
]


def annotation():
    text = '¿Qué es SQL?'
    labels = {'approaches': ['factual_tecnico'], 'main_approach': 'factual_tecnico', 'secondary_approaches': [], 'main_approach_reason': None, 'forms': ['abierta'], 'main_form': 'abierta', 'main_form_reason': None, 'attributes': [], 'certainty': 'clara', 'rationale': 'Explicación técnica solicitada.'}
    return to_wire({'contract_version': '1.1.0', 'intervention_id': 'integracion-001', 'original_text': text, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels, 'units': [{'unit_id': 'u1', 'quote': text, 'classification': deepcopy(labels), 'context_status': 'no_necesario', 'followup_of': None, 'depends_on': None}], 'context_turn_ids': [], 'rationale': 'Petición de entrevista de prueba.'})


def envelope(provider, model, text, reason="stop"):
    if provider == "ollama":
        return {"model": model, "done": True, "done_reason": reason,
                "message": {"role": "assistant", "content": text}, "prompt_eval_count": 100, "eval_count": 50}
    if provider == "unab":
        return {"model": model, "choices": [{"finish_reason": reason,
                "message": {"role": "assistant", "content": text}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
    return {"model": model, "status": "completed", "output": [{"type": "message", "role": "assistant",
            "status": "completed", "content": [{"type": "output_text", "text": text}]}],
            "usage": {"input_tokens": 100, "output_tokens": 50}}


@pytest.mark.parametrize("environ", ENVIRONMENTS)
def test_existing_adapters_use_independent_model_budget_and_auth_without_touching_candidate(environ):
    provider = environ["LLM_PROVIDER"]
    original = deepcopy(environ)
    requests = []
    model = "gemma4:e4b" if provider == "ollama" else "modelo-clasificador"
    def handler(request):
        requests.append(request)
        payload = json.loads(request.content)
        assert payload["model"] == model
        messages = payload["input"] if provider == "openai" else payload["messages"]
        assert [m["role"] for m in messages] == ["system", "user"]
        assert json.loads(messages[-1]["content"])["input"]["text"] == "¿Qué es SQL?"
        if provider == "ollama":
            assert request.url.host == "127.0.0.1" and request.url.path == "/api/chat"
            assert payload["options"]["num_predict"] == 1024
            assert "authorization" not in request.headers
        else:
            assert request.url.host == ("quotas.devhub.cl" if provider == "unab" else "api.openai.com")
            assert request.headers["authorization"] == "Bearer clave-ficticia-solo-pruebas"
            assert "clave-ficticia-solo-pruebas" not in request.content.decode("utf-8")
            assert payload["max_tokens" if provider == "unab" else "max_output_tokens"] == 1024
        return httpx.Response(200, json=envelope(provider, model, json.dumps(annotation())))
    transport = httpx.MockTransport(handler)
    with create_client(environ, transport=transport) as candidate:
        candidate_settings = candidate.settings
        with create_classification_client(environ, settings=ClassificationLLMSettings(model, 1024), transport=transport) as classifier:
            assert not requests
            report = LLMQuestionClassifier(classifier).classify("¿Qué es SQL?", intervention_id="integracion-001")
            assert report.status == "clasificada", report.to_dict()
            assert report.attempts[0].input_tokens == 100
            assert len(requests) == 1
        assert candidate.settings == candidate_settings
        assert candidate.settings.max_output_tokens == (2048 if provider == "unab" else 512)
    assert environ == original


@pytest.mark.parametrize("environ", ENVIRONMENTS)
def test_classifier_can_inherit_model_without_inheriting_candidate_output_budget(environ):
    with create_client(environ, transport=httpx.MockTransport(lambda _: pytest.fail("Sin solicitudes"))) as candidate:
        with create_classification_client(environ, transport=httpx.MockTransport(lambda _: pytest.fail("Sin solicitudes"))) as classifier:
            assert candidate.settings.model == classifier.settings.model
            assert classifier.settings.max_output_tokens == 2048
            assert candidate.settings.max_output_tokens == (2048 if environ["LLM_PROVIDER"] == "unab" else 512)


def test_unab_invalid_json_is_regenerated_once_with_same_budget_and_no_raw_replay():
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        content = "SALIDA_INVALIDA_PRIVADA" if len(calls) == 1 else json.dumps(annotation())
        return httpx.Response(200, json=envelope("unab", payload["model"], content))
    with create_classification_client(ENVIRONMENTS[1], transport=httpx.MockTransport(handler)) as client:
        report = LLMQuestionClassifier(client).classify("¿Qué es SQL?", intervention_id="integracion-001")
        assert report.status == "clasificada" and len(calls) == 2
        assert calls[0]["max_tokens"] == calls[1]["max_tokens"] == 2048
        assert calls[0]["messages"][1] == calls[1]["messages"][1]
        assert "SALIDA_INVALIDA_PRIVADA" not in json.dumps(calls[1])
        assert "SALIDA_INVALIDA_PRIVADA" not in json.dumps(report.to_dict())


@pytest.mark.parametrize("failure", ["timeout", "authentication", "length"])
def test_unab_failure_never_retries_generation_or_increases_budget(failure):
    calls = []
    def handler(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("CUERPO_PRIVADO", request=request)
        if failure == "authentication":
            return httpx.Response(401, text="CUERPO_PRIVADO")
        return httpx.Response(200, json=envelope("unab", "gemma4:26b", json.dumps(annotation()), "length"))
    with create_classification_client(ENVIRONMENTS[1], transport=httpx.MockTransport(handler)) as client:
        report = LLMQuestionClassifier(client).classify("¿Qué es SQL?", intervention_id="integracion-001")
        assert report.status == "respaldo" and len(calls) == 1
        assert client.settings.max_output_tokens == 2048
        assert "CUERPO_PRIVADO" not in json.dumps(report.to_dict())
        assert "clave-ficticia-solo-pruebas" not in json.dumps(report.to_dict())


def test_external_client_still_needs_explicit_permission_and_model_cannot_change_destination():
    with pytest.raises(LLMConfigurationError, match="desactivada"):
        create_classification_client(ENVIRONMENTS[1] | {"LLM_ALLOW_EXTERNAL_API": "false"})
    with pytest.raises(LLMConfigurationError):
        create_classification_client(ENVIRONMENTS[0], settings=ClassificationLLMSettings("modelo-cloud", 2048))


@pytest.mark.parametrize("budget", [True, "1024", 1.5])
def test_factory_overrides_reject_non_integer_budgets_without_requests(budget):
    with pytest.raises(LLMConfigurationError):
        create_client({}, max_output_tokens=budget, transport=httpx.MockTransport(lambda _: pytest.fail("Sin red")))


def test_one_local_client_sends_separate_schema_for_each_context_window():
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=envelope("ollama","gemma4:e4b",json.dumps(annotation())))
    with create_classification_client(ENVIRONMENTS[0],transport=httpx.MockTransport(handler)) as client:
        classifier = LLMQuestionClassifier(client)
        for ids in ((), (2,), (2,3), ()):
            turns = [{"turn_number":n,"messages":[{"role":"user","content":"Contexto de prueba."}]} for n in ids]
            result = classifier.classify("¿Qué es SQL?",intervention_id="integracion-001",context_turns=turns)
            assert result.status == "clasificada"
            assert calls[-1]["format"] == classification_generation_schema(allowed_context_turn_ids=ids)
        client.generate([{"role":"user","content":"Prueba del formato por defecto."}])
    assert len(calls) == 5 and calls[-1]["format"] == classification_generation_schema()
    assert calls[0]["format"] == calls[3]["format"]
    assert all(c["options"]["num_predict"] == 2048 for c in calls)


def test_native_context_constraints_do_not_replace_cross_field_validation():
    calls = []
    invalid = annotation()
    invalid["context_turn_ids"] = [2]
    invalid["units"][0].update(followup_of=3,context_status="suficiente")
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=envelope("ollama","gemma4:e4b",json.dumps(invalid)))
    turns = [{"turn_number":n,"messages":[{"role":"user","content":"Contexto de prueba."}]} for n in (2,3)]
    with create_classification_client(ENVIRONMENTS[0],transport=httpx.MockTransport(handler)) as client:
        report=LLMQuestionClassifier(client).classify("¿Qué es SQL?",intervention_id="integracion-001",context_turns=turns)
    assert report.status == "respaldo" and len(calls) == 2
    assert all(a.validation_error.rule == "followup_scope" for a in report.attempts)
    assert calls[0]["format"] == calls[1]["format"]


def test_classifier_prompt_mode_keeps_native_format_disabled():
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json=envelope("ollama","gemma4:e4b",json.dumps(annotation())))
    with create_classification_client(ENVIRONMENTS[0],structured_output=False,transport=httpx.MockTransport(handler)) as client:
        assert LLMQuestionClassifier(client).classify("¿Qué es SQL?",intervention_id="integracion-001").status == "clasificada"
    assert len(calls) == 1 and "format" not in calls[0]

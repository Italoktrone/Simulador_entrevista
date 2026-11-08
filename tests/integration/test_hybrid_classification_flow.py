"""Híbrido completo sobre adaptadores con HTTP simulado, sin candidato ni red."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
import json

import httpx
import pytest

from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.llm_question_classifier import LLMQuestionClassifier, create_classification_client


TEXT = "Describe la utilidad de un registro de eventos."
ENVIRONMENTS = [
    {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "gemma4:e4b"},
    {"LLM_PROVIDER": "unab", "LLM_ALLOW_EXTERNAL_API": "true", "UNAB_MODEL": "gemma4:26b",
     "UNAB_API_KEY": "clave-ficticia-solo-pruebas"},
    {"LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true", "OPENAI_MODEL": "modelo-simulado",
     "OPENAI_API_KEY": "clave-ficticia-solo-pruebas"},
]


def labels(approach="factual_tecnico", form="abierta"):
    return {"approaches": [approach], "main_approach": approach, "secondary_approaches": [],
            "main_approach_reason": None, "forms": [form], "main_form": form, "main_form_reason": None,
            "attributes": [], "certainty": "clara", "rationale": "Anotación sintética para verificar el flujo."}


def unit(text, number=1, approach="factual_tecnico", form="abierta"):
    return {"unit_id": f"u{number}", "quote": text,
            "classification": labels(approach, form), "context_status": "no_necesario",
            "followup_of": None, "depends_on": None}


def annotation(text=TEXT):
    return to_wire({'contract_version': '1.1.0', 'intervention_id': 'flujo-001', 'original_text': text, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels(), 'units': [unit(text)], 'context_turn_ids': [], 'rationale': 'Caso técnico sintético.'})


def envelope(provider, model, text):
    if provider == "ollama":
        return {"model": model, "done": True, "done_reason": "stop",
                "message": {"role": "assistant", "content": text}}
    if provider == "unab":
        return {"model": model, "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": text}}]}
    return {"model": model, "status": "completed", "output": [{"type": "message", "role": "assistant",
            "status": "completed", "content": [{"type": "output_text", "text": text}]}]}


@pytest.mark.parametrize("environ", ENVIRONMENTS)
def test_local_route_works_without_contacting_even_an_unavailable_backend(environ):
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("No se debe alcanzar el backend", request=request)
    with create_classification_client(environ, transport=httpx.MockTransport(handler)) as client:
        classifier = HybridQuestionClassifier(LLMQuestionClassifier(client))
        for text in ("¿Has usado Git?", "Entiendo", "¿Qué pasó después?"):
            report = classifier.classify(text, intervention_id="flujo-001")
            assert report.route == "reglas" and report.status == "clasificada"
            assert report.trace["llm"] is None
    assert calls == []


@pytest.mark.parametrize("environ", ENVIRONMENTS)
def test_abstention_reaches_existing_client_once_and_preserves_effective_llm_method(environ):
    calls = []
    provider = environ["LLM_PROVIDER"]
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        messages = payload["input"] if provider == "openai" else payload["messages"]
        assert json.loads(messages[-1]["content"])["input"]["text"] == TEXT
        return httpx.Response(200, json=envelope(provider, payload["model"], json.dumps(annotation())))
    with create_classification_client(environ, transport=httpx.MockTransport(handler)) as client:
        report = HybridQuestionClassifier(LLMQuestionClassifier(client)).classify(TEXT, intervention_id="flujo-001")
    assert report.route == "llm" and report.status == "clasificada" and len(calls) == 1
    assert report.result["method"] == "llm" and report.result["rule_ids"] == []
    assert report.trace["local"]["status"] == "abstencion"
    assert report.trace["llm"]["attempts"][0]["status"] == "validada"


def test_one_semantic_request_handles_entire_compound_without_per_unit_calls_or_fake_mixed_labels():
    first, second = "¿Conoces Git?", "¿Cómo actuarías si una entrega fallara?"
    text = first + " " + second
    expected = annotation(text)
    expected["classification"].update(main_approach=None, main_form=None)
    expected["units"] = [unit(first, form="cerrada"), unit(second, 2, "situacional")]
    expected = to_wire(expected)
    before = deepcopy(expected)
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        return httpx.Response(200, json=envelope("unab", payload["model"], json.dumps(expected)))
    with create_classification_client(ENVIRONMENTS[1], transport=httpx.MockTransport(handler)) as client:
        report = HybridQuestionClassifier(LLMQuestionClassifier(client)).classify(text, intervention_id="flujo-001")
    assert len(calls) == 1 and expected == before
    assert report.result["method"] == "llm"
    assert [entry["method"] for entry in report.result["units"]] == ["llm", "llm"]
    assert report.result["classification"]["main_approach"] is None
    assert report.result["classification"]["main_form"] is None
    assert report.to_dict()["strategy"] == "reglas_luego_llm"


def test_repair_budget_is_owned_by_interpreter_and_not_multiplied_by_router():
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        content = "SALIDA_PRIVADA_INVALIDA" if len(calls) == 1 else json.dumps(annotation())
        return httpx.Response(200, json=envelope("unab", payload["model"], content))
    with create_classification_client(ENVIRONMENTS[1], transport=httpx.MockTransport(handler)) as client:
        report = HybridQuestionClassifier(LLMQuestionClassifier(client)).classify(TEXT, intervention_id="flujo-001")
    assert len(calls) == 2 and report.status == "clasificada"
    assert calls[0]["max_tokens"] == calls[1]["max_tokens"] == 2048
    assert calls[0]["messages"][-1] == calls[1]["messages"][-1]
    assert len(report.trace["llm"]["attempts"]) == 2
    assert "SALIDA_PRIVADA_INVALIDA" not in json.dumps(report.to_dict())


def test_provider_failure_keeps_validated_fallback_without_trying_another_provider_or_candidate():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(401, text="CUERPO_PRIVADO_NO_REGISTRAR")
    with create_classification_client(ENVIRONMENTS[1], transport=httpx.MockTransport(handler)) as client:
        report = HybridQuestionClassifier(LLMQuestionClassifier(client)).classify(TEXT, intervention_id="flujo-001")
    assert len(calls) == 1 and report.status == "respaldo" and report.route == "llm"
    assert report.result["method"] == "respaldo" and report.result["technical_error"] == "error_proveedor"
    assert report.trace["llm"]["attempts"][0]["error_code"] == "authentication_error"
    serialized = json.dumps(report.to_dict())
    assert "CUERPO_PRIVADO_NO_REGISTRAR" not in serialized
    assert "clave-ficticia-solo-pruebas" not in serialized

"""Regresión completa de entrevista, adaptadores y herramientas con HTTP simulado."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
import json
from pathlib import Path

import httpx
import pytest

from harness.history_summary import build_summary_source
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMProviderError
from harness.llm.factory import create_client
from harness.llm_question_classifier import (
    ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)
from harness.prompt_builder import load_instructions
from harness.response_policy import ResponsePolicyDecision
from harness.runtime import InterviewRuntime
from harness.session_log import load_session, save_session
from scripts import inspect_context, preview_summary


ENVIRONMENTS = [
    {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "gemma4:e4b"},
    {"LLM_PROVIDER": "unab", "LLM_ALLOW_EXTERNAL_API": "true", "UNAB_MODEL": "gemma4:26b",
     "UNAB_API_KEY": "CLAVE_FICTICIA_REGRESION", "UNAB_MAX_OUTPUT_TOKENS": "1536"},
    {"LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true", "OPENAI_MODEL": "modelo-candidato",
     "OPENAI_API_KEY": "CLAVE_FICTICIA_REGRESION"},
]
ROOT = Path(__file__).resolve().parents[2]
PROTECTED = [ROOT / path for path in (
    "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
    "config/interviews/basica.json", "agent/agent.md",
    "data/reference_questions/clasificacion_basica.json",
)]
FIRST = "Describe la utilidad de un registro de eventos."
FAILED = "Explica cómo lo aplicarías a ese caso."
LAST = "Describe una estrategia para revisar esa actuación."
INVALID = "SALIDA_RECHAZADA_NO_REENVIAR"
PRIVATE_BODY = "CUERPO_HTTP_NO_REGISTRAR"


def annotation(data, *, followup=False):
    text = data['text']
    labels = {'approaches': ['factual_tecnico'], 'main_approach': 'factual_tecnico', 'secondary_approaches': [], 'main_approach_reason': None, 'forms': ['abierta'], 'main_form': 'abierta', 'main_form_reason': None, 'attributes': [], 'certainty': 'clara', 'rationale': 'RAZON_LIBRE_NO_ES_ORDEN'}
    previous = data['context_turns'][-1]['turn_number'] if followup else None
    return to_wire({'contract_version': '1.1.0', 'intervention_id': data['intervention_id'], 'original_text': text, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels, 'units': [{'unit_id': 'u1', 'quote': text, 'classification': deepcopy(labels), 'context_status': 'suficiente' if followup else 'no_necesario', 'followup_of': previous, 'depends_on': None}], 'context_turn_ids': [previous] if followup else [], 'rationale': 'Prueba sintética de flujo.'})


def envelope(provider, model, text, *, incomplete=False):
    if provider == "ollama":
        return {"model": model, "done": True, "done_reason": "length" if incomplete else "stop",
                "message": {"role": "assistant", "content": text}, "prompt_eval_count": 100, "eval_count": 50}
    if provider == "unab":
        return {"model": model, "choices": [{"finish_reason": "length" if incomplete else "stop",
                "message": {"role": "assistant", "content": text}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
    result = {"model": model, "status": "incomplete" if incomplete else "completed", "output": [
              {"type": "message", "role": "assistant", "status": "completed",
               "content": [{"type": "output_text", "text": text}]}],
              "usage": {"input_tokens": 100, "output_tokens": 50}}
    if incomplete:
        result["incomplete_details"] = {"reason": "max_output_tokens"}
    return result


def messages(payload, provider):
    return payload["input" if provider == "openai" else "messages"]


def budget(payload, provider):
    if provider == "ollama":
        return payload["options"]["num_predict"]
    return payload["max_output_tokens" if provider == "openai" else "max_tokens"]


@pytest.mark.parametrize("environ", ENVIRONMENTS, ids=["ollama", "unab", "responses"])
def test_repair_failure_recovery_and_existing_tools_preserve_history_and_sources(
    environ, tmp_path, monkeypatch, capsys,
):
    before = {path: path.read_bytes() for path in PROTECTED}
    provider = environ["LLM_PROVIDER"]
    events, classifier_requests, candidate_requests = [], [], []
    candidate_text = "Respuesta histórica completa. Referencia conservada."

    def classification_handler(request):
        events.append("classifier")
        payload = json.loads(request.content)
        classifier_requests.append(payload)
        data = json.loads(messages(payload, provider)[-1]["content"])["input"]
        content = INVALID if len(classifier_requests) == 1 else json.dumps(annotation(data, followup=data["text"] == FAILED))
        return httpx.Response(200, json=envelope(provider, payload["model"], content))

    def candidate_handler(request):
        events.append("candidate")
        payload = json.loads(request.content)
        candidate_requests.append(payload)
        if len(candidate_requests) == 2:
            return httpx.Response(500, text=PRIVATE_BODY)
        return httpx.Response(200, json=envelope(provider, payload["model"], candidate_text))

    with create_client(environ, transport=httpx.MockTransport(candidate_handler)) as candidate:
        with create_classification_client(environ, settings=ClassificationLLMSettings(max_output_tokens=1024),
                                         transport=httpx.MockTransport(classification_handler)) as semantic:
            runtime = InterviewRuntime(load_interview_setup(), load_instructions(), candidate,
                                       provider=provider, model=candidate.settings.model,
                                       classifier=HybridQuestionClassifier(LLMQuestionClassifier(semantic)))
            assert runtime.ask("Hola").action == "no_evaluable"
            assert events == [] and runtime.questions_asked == 0
            assert runtime.ask(FIRST).text == candidate_text
            with pytest.raises(LLMProviderError):
                runtime.ask(FAILED)
            assert runtime.questions_asked == 2
            assert runtime.ask(LAST).text == candidate_text
            assert runtime.questions_asked == 3
            runtime.close("user_exit")
            path = save_session(runtime.session_dict(), tmp_path / "records")

    assert candidate._http.is_closed and semantic._http.is_closed
    assert events == ["classifier", "classifier", "candidate", "classifier", "candidate", "classifier", "candidate"]
    assert {budget(payload, provider) for payload in classifier_requests} == {1024}
    assert {budget(payload, provider) for payload in candidate_requests} == ({1536} if provider == "unab" else {512})
    assert messages(classifier_requests[0], provider)[-1] == messages(classifier_requests[1], provider)[-1]
    assert INVALID not in json.dumps(classifier_requests[1])
    final_context = json.loads(messages(classifier_requests[-1], provider)[-1]["content"])["input"]["context_turns"]
    assert [turn["turn_number"] for turn in final_context] == [1]
    final_messages = messages(candidate_requests[-1], provider)
    assert [m["role"] for m in final_messages] == ["system", "user", "assistant", "user"]
    assert [m["content"] for m in final_messages[1:]] == [FIRST, candidate_text, LAST]
    assert "CLASIFICACION_DESCRIPTIVA_JSON" in final_messages[0]["content"]
    assert "RAZON_LIBRE_NO_ES_ORDEN" not in final_messages[0]["content"]

    record = load_session(path)
    assert record["session_version"] == "1.2.0"
    assert [a["status"] for a in record["attempts"]] == ["completed", "error", "completed"]
    assert [i["status"] for i in record["interventions"]] == ["handled", "completed", "error", "completed"]
    assert [i["candidate_question_number"] for i in record["interventions"]] == [None, 1, 2, 3]
    assert len(record["interventions"][1]["classification"]["trace"]["llm"]["attempts"]) == 2
    assert record["interventions"][2]["classification"]["result"]["context_turn_ids"] == [1]
    assert [turn["question_number"] for turn in build_summary_source(record)["recent_turns"]] == [1, 3]
    serialized = json.dumps(record)
    assert all(value not in serialized for value in (INVALID, PRIVATE_BODY, "CLAVE_FICTICIA_REGRESION"))

    files_before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    monkeypatch.setattr(preview_summary, "create_client", lambda: pytest.fail("La vista de pares recientes no necesita proveedor"))
    assert inspect_context.main([str(path)]) == 0
    report = capsys.readouterr().out
    assert "Pregunta 2 (error)" in report and "Intentos sin métrica de entrada: 1" in report
    assert all(value not in report for value in (FIRST, FAILED, LAST, candidate_text))
    assert preview_summary.main([str(path), "--keep-recent-pairs", "20"]) == 0
    preview = capsys.readouterr().out
    assert FIRST in preview and LAST in preview and FAILED not in preview and "Hola" not in preview
    assert files_before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == {path: path.read_bytes() for path in PROTECTED}


@pytest.mark.parametrize("environ", ENVIRONMENTS, ids=["ollama", "unab", "responses"])
@pytest.mark.parametrize("failure", ["invalid_twice", "authentication", "timeout", "length"])
def test_terminal_classifier_failure_allows_local_recovery_without_spending_candidate_attempt(
    environ, failure, tmp_path,
):
    provider = environ["LLM_PROVIDER"]
    classifier_requests, candidate_requests = [], []

    def classification_handler(request):
        classifier_requests.append(json.loads(request.content))
        if failure == "authentication":
            return httpx.Response(401, text=PRIVATE_BODY)
        if failure == "timeout":
            raise httpx.ReadTimeout(PRIVATE_BODY, request=request)
        payload = classifier_requests[-1]
        return httpx.Response(200, json=envelope(provider, payload["model"], INVALID, incomplete=failure == "length"))

    def candidate_handler(request):
        candidate_requests.append(json.loads(request.content))
        return httpx.Response(200, json=envelope(provider, candidate_requests[-1]["model"], "Respuesta recuperada."))

    with create_client(environ, transport=httpx.MockTransport(candidate_handler)) as candidate:
        with create_classification_client(environ, transport=httpx.MockTransport(classification_handler)) as semantic:
            runtime = InterviewRuntime(load_interview_setup(), load_instructions(), candidate,
                                       classifier=HybridQuestionClassifier(LLMQuestionClassifier(semantic)))
            notice = runtime.ask(FIRST)
            assert isinstance(notice, ResponsePolicyDecision) and notice.action == "error_tecnico"
            assert runtime.questions_asked == 0 and candidate_requests == []
            expected = 2 if failure == "invalid_twice" else 1
            assert len(classifier_requests) == expected
            assert runtime.ask("¿Has usado Git?").text == "Respuesta recuperada."
            assert len(classifier_requests) == expected and len(candidate_requests) == 1
            runtime.close()
            record = load_session(save_session(runtime.session_dict(), tmp_path / "records"))

    assert candidate._http.is_closed and semantic._http.is_closed
    assert record["attempts"][0]["question_number"] == 1
    assert [i["candidate_question_number"] for i in record["interventions"]] == [None, 1]
    assert record["interventions"][0]["classification"]["result"]["method"] == "respaldo"
    assert record["interventions"][1]["classification"]["result"]["method"] == "reglas"
    assert {budget(payload, provider) for payload in classifier_requests} == {2048}
    assert all(value not in json.dumps(record) for value in (INVALID, PRIVATE_BODY, "CLAVE_FICTICIA_REGRESION"))

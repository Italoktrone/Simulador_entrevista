"""Enrutamiento y contratos del híbrido con cliente sintético, no semántica real."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

import pytest

from harness import hybrid_question_classifier
from harness.classification_contract import validate_classification
from harness.classification_references import load_classification_references
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.llm.client import LLMResponse, LLMProviderError
from harness.llm_question_classifier import LLMQuestionClassifier


TEXT = "Describe la función de una herramienta de control de versiones."


def draft(text=TEXT, *, intervention_id='hybrid-001', approach='factual_tecnico', form='abierta'):
    labels = {'approaches': [approach], 'main_approach': approach, 'secondary_approaches': [], 'main_approach_reason': None, 'forms': [form], 'main_form': form, 'main_form_reason': None, 'attributes': [], 'certainty': 'clara', 'rationale': 'Etiquetas sintéticas para probar la ruta.'}
    return to_wire({'contract_version': '1.1.0', 'intervention_id': intervention_id, 'original_text': text, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels, 'units': [{'unit_id': 'u1', 'quote': text, 'classification': deepcopy(labels), 'context_status': 'no_necesario', 'followup_of': None, 'depends_on': None}], 'context_turn_ids': [], 'rationale': 'Intervención de prueba para el coordinador.'})


def response(value, finish_reason="stop"):
    return LLMResponse(value if isinstance(value, str) else json.dumps(value),
                       "modelo-simulado", "ollama", 0.1, input_tokens=20, output_tokens=10,
                       finish_reason=finish_reason)


class FakeClient:
    def __init__(self, *items):
        self.items = list(items)
        self.calls = []

    def generate(self, messages):
        self.calls.append(deepcopy(messages))
        if not self.items:
            raise LLMProviderError("FALLO_SIMULADO_SIN_CUERPO_PUBLICO")
        item = self.items.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class RecordingInterpreter(LLMQuestionClassifier):
    def __init__(self, client, events):
        super().__init__(client)
        self.events = events
        self.invocations = []

    def classify(self, **kwargs):
        self.events.append("llm")
        self.invocations.append(deepcopy(kwargs))
        return super().classify(**kwargs)


def hybrid(client=None):
    return HybridQuestionClassifier(LLMQuestionClassifier(FakeClient() if client is None else client))


@pytest.mark.parametrize("text", ["¿Conoces SQL?", "Hola", "Gracias por tu respuesta", "", "   ", "¿Qué ocurrió después?"])
def test_local_result_returns_without_any_llm_call_even_when_non_evaluable_or_undetermined(text):
    client = FakeClient()
    report = hybrid(client).classify(text, intervention_id="hybrid-001")
    assert report.route == "reglas" and report.status == "clasificada"
    assert report.result["method"] == "reglas"
    assert report.trace["llm"] is None and client.calls == []
    assert report.result == validate_classification(report.result, expected_intervention_id="hybrid-001", expected_text=text)
    if text == "¿Qué ocurrió después?":
        assert report.result["classification"]["certainty"] == "indeterminada"
        assert report.result["technical_error"] is None


def test_order_one_local_evaluation_and_one_interpreter_invocation_with_original_input(monkeypatch):
    events = []
    original_local = hybrid_question_classifier.classify_local
    def local(**kwargs):
        events.append("local")
        return original_local(**kwargs)
    monkeypatch.setattr(hybrid_question_classifier, "classify_local", local)
    client = FakeClient(response(draft()))
    interpreter = RecordingInterpreter(client, events)
    report = HybridQuestionClassifier(interpreter).classify(TEXT, intervention_id="hybrid-001")
    assert events == ["local", "llm"] and len(interpreter.invocations) == len(client.calls) == 1
    assert interpreter.invocations[0]["text"] == TEXT
    assert report.route == "llm" and report.result["method"] == "llm"
    assert report.trace["local"]["status"] == "abstencion"
    assert report.trace["llm"]["attempts"][0]["status"] == "validada"
    assert report.result["rule_ids"] == []
    assert "result" not in report.trace["local"] and "result" not in report.trace["llm"]
    assert "original_text" not in report.trace["local"]
    assert "reason_code" not in json.loads(client.calls[0][1]["content"])["input"]


def test_contextual_followup_goes_to_interpreter_without_inheriting_a_local_label():
    text = "¿Qué hiciste después?"
    proposed = draft(text, approach="conductual")
    proposed["context_turn_ids"] = [1]
    proposed["units"][0].update(context_status="suficiente", followup_of=1)
    turns = [{"turn_number": 1, "messages": [{"role": "assistant", "content": "La coordinadora detectó solicitudes ausentes."}]}]
    before = deepcopy(turns)
    client = FakeClient(response(proposed))
    report = hybrid(client).classify(text, intervention_id="hybrid-001", context_turns=turns)
    assert report.route == "llm" and report.result["classification"]["main_approach"] == "conductual"
    assert report.trace["local"]["reason_code"] == "contexto_requiere_interpretacion"
    assert json.loads(client.calls[0][1]["content"])["input"]["context_turns"] == turns
    assert turns == before


def test_one_interpreter_invocation_owns_its_only_json_repair_without_outer_retry():
    client = FakeClient(response("JSON_INVALIDO_PRIVADO"), response(draft()), response(draft()))
    interpreter = RecordingInterpreter(client, [])
    report = HybridQuestionClassifier(interpreter).classify(TEXT, intervention_id="hybrid-001")
    assert len(interpreter.invocations) == 1 and len(client.calls) == 2
    assert report.status == "clasificada" and report.result["method"] == "llm"
    assert [attempt["status"] for attempt in report.trace["llm"]["attempts"]] == ["json_invalido", "validada"]
    assert "JSON_INVALIDO_PRIVADO" not in json.dumps(report.to_dict())


@pytest.mark.parametrize("items", [
    (response("{"), response("{"), response(draft())),
    (LLMProviderError("CUERPO_NO_REGISTRAR"), response(draft())),
    (response(draft(), "length"), response(draft())),
])
def test_terminal_llm_failure_returns_same_technical_fallback_without_reclassifying(items):
    client = FakeClient(*items)
    interpreter = RecordingInterpreter(client, [])
    report = HybridQuestionClassifier(interpreter).classify(TEXT, intervention_id="hybrid-001")
    assert report.route == "llm" and report.status == "respaldo"
    assert report.result["method"] == "respaldo" and report.result["evaluability"] is None
    assert report.result["validation_status"] == "validada" and report.result["units"] == []
    assert len(interpreter.invocations) == 1
    assert len(client.calls) == (2 if len(items) == 3 else 1)
    assert "CUERPO_NO_REGISTRAR" not in json.dumps(report.to_dict())


def test_an_unsupported_nonevaluable_intervention_can_be_classified_by_llm():
    text = "Buen día y muchas gracias por recibir este mensaje."
    proposed = draft(text)
    proposed.update(evaluability="no_evaluable", non_evaluable_reason="saludo", classification=None, units=[])
    report = hybrid(FakeClient(response(proposed))).classify(text, intervention_id="hybrid-001")
    assert report.route == "llm" and report.result["classification"] is None
    assert report.result["evaluability"] == "no_evaluable" and report.result["method"] == "llm"


def test_results_and_traces_are_copies_and_the_router_has_no_previous_interview_state():
    client = FakeClient(response(draft()))
    classifier = hybrid(client)
    first = classifier.classify(TEXT, intervention_id="hybrid-001")
    original = first.to_dict()
    first.result["units"].clear()
    first.trace["llm"]["attempts"].clear()
    assert first.to_dict() == original
    with pytest.raises(FrozenInstanceError):
        first.route = "reglas"
    next_report = classifier.classify("¿Conoces SQL?", intervention_id="otra-intervencion")
    assert next_report.route == "reglas" and next_report.trace["llm"] is None
    assert next_report.result["intervention_id"] == "otra-intervencion"
    assert len(client.calls) == 1 and first.to_dict() == original


def test_snapshot_does_not_expose_caller_mutations_to_interpreter(monkeypatch):
    turns = [{"turn_number": 1, "messages": [{"role": "assistant", "content": "CONTEXTO_ORIGINAL"}]}]
    original_local = hybrid_question_classifier.classify_local
    def local(**kwargs):
        decision = original_local(**kwargs)
        turns[0]["messages"][0]["content"] = "CAMBIO_EXTERNO"
        return decision
    monkeypatch.setattr(hybrid_question_classifier, "classify_local", local)
    client = FakeClient(response(draft()))
    hybrid(client).classify(TEXT, intervention_id="hybrid-001", context_turns=turns)
    received = json.loads(client.calls[0][1]["content"])["input"]["context_turns"]
    assert received[0]["messages"][0]["content"] == "CONTEXTO_ORIGINAL"


@pytest.mark.parametrize("kwargs", [
    {"intervention_id": "invalido\n"}, {"text": None}, {"text": "\ud800"},
    {"context_turns": "No es historial"}, {"competency": " "},
    {"context_turns": [{"turn_number": 1, "messages": [{"role": "system", "content": "NO_ENVIAR"}]}]},
])
def test_invalid_input_reaches_no_semantic_generation(kwargs):
    client = FakeClient(response(draft()))
    params = {"text": TEXT, "intervention_id": "hybrid-001"} | kwargs
    with pytest.raises(ValueError):
        hybrid(client).classify(**params)
    assert client.calls == []


def test_unconfigured_interpreter_is_a_program_configuration_error():
    with pytest.raises(ValueError, match="LLMQuestionClassifier"):
        HybridQuestionClassifier(None)


def test_cancellation_propagates_without_another_interpreter_invocation():
    client = FakeClient(KeyboardInterrupt(), response(draft()))
    interpreter = RecordingInterpreter(client, [])
    with pytest.raises(KeyboardInterrupt):
        HybridQuestionClassifier(interpreter).classify(TEXT, intervention_id="hybrid-001")
    assert len(interpreter.invocations) == len(client.calls) == 1


def test_development_routing_is_16_local_and_14_semantic_with_explicit_simulated_failures():
    # No se usan respuestas esperadas como respuestas del modelo. Todos los
    # fallos semánticos son deliberados para contar delegaciones, no acierto.
    suite = load_classification_references()
    client = FakeClient()
    interpreter = RecordingInterpreter(client, [])
    classifier = HybridQuestionClassifier(interpreter)
    routes = {"reglas": 0, "llm": 0}
    for case in suite.cases():
        report = classifier.classify(**suite.input_for(case["case_id"]))
        routes[report.route] += 1
        assert report.status == ("clasificada" if report.route == "reglas" else "respaldo")
    assert routes == {"reglas": 16, "llm": 14}
    assert len(interpreter.invocations) == len(client.calls) == 14


def test_source_files_and_approved_cases_remain_intact():
    root = Path(__file__).resolve().parents[2]
    paths = [root / name for name in ("data/candidates/candidato_junior.json", "agent/agent.md",
                                     "config/interviews/basica.json", "data/jobs/desarrollador_junior.json",
                                     "data/reference_questions/clasificacion_basica.json")]
    before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    hybrid().classify("¿Conoces SQL?", intervention_id="hybrid-001")
    hybrid(FakeClient(response(draft()))).classify(TEXT, intervention_id="hybrid-001")
    assert [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths] == before

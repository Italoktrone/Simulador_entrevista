"""Clasificación -> política -> candidato y sesiones 1.2, todo simulado."""

from copy import deepcopy
from tests.wire_fixtures import to_wire
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.interview_config import load_interview_setup
from harness.intervention_log import select_classification_context
from harness.llm.client import LLMResponse, LLMTimeoutError, LLMProviderError
from harness.llm.factory import create_client
from harness.llm_question_classifier import LLMQuestionClassifier, create_classification_client
from harness.live_context import LiveContextPolicy
from harness.history_summary import SELECTION_INSTRUCTIONS
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.response_policy import ResponsePolicyDecision
from harness.runtime import InterviewFinishedError, InterviewRuntime
from harness.session_log import SessionLogError, load_session, save_session
from scripts import run_interview, start_interview


def answer(text="Respuesta simulada del candidato.", **kwargs):
    return LLMResponse(text, "modelo-simulado", "ollama", 0.1, input_tokens=6100,
                       finish_reason="stop", **kwargs)


def annotation(data, *, approach='factual_tecnico', form='abierta', certainty='clara', followup=False):
    text = data['text']
    labels = {'approaches': [approach], 'main_approach': approach, 'secondary_approaches': [], 'main_approach_reason': None, 'forms': [form], 'main_form': form, 'main_form_reason': None, 'attributes': [], 'certainty': certainty, 'rationale': 'JUSTIFICACION_LIBRE_NO_AUTORIZADA'}
    ids = [data['context_turns'][-1]['turn_number']] if followup else []
    context_status = 'suficiente' if followup else 'insuficiente' if certainty != 'clara' else 'no_necesario'
    return to_wire({'contract_version': '1.1.0', 'intervention_id': data['intervention_id'], 'original_text': text, 'evaluability': 'evaluable', 'non_evaluable_reason': None, 'classification': labels, 'units': [{'unit_id': 'u1', 'quote': text, 'classification': deepcopy(labels), 'context_status': context_status, 'followup_of': ids[0] if ids else None, 'depends_on': None}], 'context_turn_ids': ids, 'rationale': 'Intervención sintética para comprobar el flujo.'})


class SemanticClient:
    def __init__(self, *, mode="valid", events=None, callback=None):
        self.mode = mode
        self.events = [] if events is None else events
        self.callback = callback
        self.requests = []

    def generate(self, messages):
        data = json.loads(messages[1]["content"])["input"]
        self.requests.append(deepcopy(data))
        self.events.append("classifier_llm")
        if self.callback:
            self.callback(data)
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        if self.mode == "provider_error":
            raise LLMProviderError("CUERPO_PRIVADO_NO_REGISTRAR")
        if self.mode == "invalid":
            return answer("SALIDA_PRIVADA_INVALIDA")
        if self.mode == "ambiguous":
            result = annotation(data, certainty="ambigua")
        elif self.mode == "followup":
            result = annotation(data, approach="conductual", followup=True)
        else:
            result = annotation(data)
        return answer(json.dumps(result))


class CandidateClient:
    def __init__(self, *, events=None, outcomes=None, callback=None):
        self.events = [] if events is None else events
        self.outcomes = list(outcomes or [])
        self.callback = callback
        self.requests = []
        self.selections = 0

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        if messages[0]["content"] == SELECTION_INSTRUCTIONS:
            self.selections += 1
            source = json.loads(messages[1]["content"])
            return answer(json.dumps({"selections": [{"question_number": turn["question_number"],
                           "segment_indices": turn["required_segment_indices"]} for turn in source["old_turns"]]}))
        self.events.append("candidate")
        if self.callback:
            self.callback(messages)
        outcome = self.outcomes.pop(0) if self.outcomes else answer()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def make_runtime(*, semantic=None, candidate=None, context_policy=None, setup=None):
    semantic = SemanticClient() if semantic is None else semantic
    candidate = CandidateClient() if candidate is None else candidate
    classifier = HybridQuestionClassifier(LLMQuestionClassifier(semantic))
    runtime = InterviewRuntime(load_interview_setup() if setup is None else setup, load_instructions(), candidate,
                               classifier=classifier, context_policy=context_policy)
    return runtime, semantic, candidate


def roundtrip(runtime, tmp_path):
    runtime.close()
    return load_session(save_session(runtime.session_dict(), tmp_path / "records"))


def test_contract_audit_roundtrip_and_legacy_compatibility(tmp_path):
    class InvalidContract(SemanticClient):
        def generate(self, messages):
            data = json.loads(messages[1]["content"])["input"]
            value = annotation(data)
            value["units"][0]["classification"]["rationale"] = ""
            return answer(json.dumps(value))
    runtime, _, candidate = make_runtime(semantic=InvalidContract())
    runtime.ask("Describe la utilidad de una herramienta de versiones.")
    record = roundtrip(runtime, tmp_path)
    attempts = record["interventions"][0]["classification"]["trace"]["llm"]["attempts"]
    assert len(attempts) == 2 and candidate.requests == []
    assert attempts[0]["validation_error"]["path"] == "/units/0/classification/rationale"
    for attempt in attempts:
        attempt.pop("validation_error")
    assert load_session(save_session(record, tmp_path / "legacy"))["attempts"] == []


@pytest.mark.parametrize("mode,contract,json_errors,provider", [("contract",1,0,0), ("invalid",0,1,0), ("provider_error",0,0,1)])
def test_summary_counts_terminal_classifier_failure_once(mode, contract, json_errors, provider):
    from harness.application.cli import format_session
    class InvalidContract(SemanticClient):
        def generate(self, messages):
            data = json.loads(messages[1]["content"])["input"]
            value = annotation(data)
            value["classification"]["rationale"] = ""
            return answer(json.dumps(value))
    semantic = InvalidContract() if mode == "contract" else SemanticClient(mode=mode)
    runtime, _, _ = make_runtime(semantic=semantic)
    runtime.ask("Describe la utilidad de una herramienta de versiones.")
    text = format_session(runtime)
    assert "Incidencias técnicas: 1" in text
    assert "Fallos de clasificación: 1" in text
    assert f"Fallos de contrato del clasificador: {contract}" in text
    assert f"Fallos de JSON del clasificador: {json_errors}" in text
    assert f"Fallos del proveedor del clasificador (incluye red/servidor): {provider}" in text
    assert "Otras incidencias técnicas (candidato/memoria/sesión): 0" in text


def test_single_intervention_diagnostic_uses_original_context_and_saves_only_safe_audit(monkeypatch, tmp_path):
    from scripts import diagnose_validation as script
    from contextlib import contextmanager
    runtime, _, _ = make_runtime()
    runtime.ask("¿Has utilizado Git para controlar versiones?")
    runtime.ask("¿Qué herramientas utilizaste en tu proyecto académico más reciente?")
    record = roundtrip(runtime, tmp_path)
    source = save_session(record, tmp_path / "source")
    before = source.read_bytes()
    class SensitiveInvalidContract(SemanticClient):
        def generate(self, messages):
            data = json.loads(messages[1]["content"])["input"]
            self.requests.append(data)
            value = annotation(data)
            value["units"][0]["classification"]["forms"] = ["sk-PRIVATE_KEY_MUST_NOT_BE_WRITTEN"]
            return answer(json.dumps(value))
    semantic = SensitiveInvalidContract()
    @contextmanager
    def fake_factory(environ, **kwargs):
        assert environ == {"LLM_PROVIDER":"ollama", "LLM_ALLOW_EXTERNAL_API":"false", "OLLAMA_MODEL":"gemma4:e4b"}
        assert kwargs["settings"].max_output_tokens == 2048
        yield semantic
    monkeypatch.setattr(script, "create_classification_client", fake_factory)
    monkeypatch.setattr(script, "ROOT", tmp_path / "report-root")
    assert script.main([str(source), "--intervention", "2"]) == 0
    paths = list((script.ROOT / "outputs/results").glob("validation-audit-*.json"))
    assert len(paths) == 1
    text = paths[0].read_text(encoding="utf-8")
    report = json.loads(text)
    assert report["context_turn_ids"] == [1] and len(semantic.requests) == 2
    assert semantic.requests[0]["context_turns"][0]["messages"][1]["content"] == record["attempts"][0]["response"]["text"]
    assert report["attempts"][0]["validation_error"]["path"] == "/units/0/classification/forms/0"
    assert "PRIVATE_KEY" not in text and "original_text" not in text
    assert source.read_bytes() == before and report["source_unchanged"]


def test_classification_and_policy_precede_candidate_and_only_enum_metadata_is_authorized(monkeypatch, tmp_path):
    from harness import runtime as runtime_module
    events = []
    semantic = SemanticClient(events=events)
    candidate = CandidateClient(events=events)
    original = runtime_module.decide_response
    def policy(*args, **kwargs):
        events.append("policy")
        return original(*args, **kwargs)
    monkeypatch.setattr(runtime_module, "decide_response", policy)
    runtime, _, _ = make_runtime(semantic=semantic, candidate=candidate)
    semantic.callback = lambda data: (len(runtime.session_dict()["attempts"]) == 0) or pytest.fail("Candidato iniciado antes de clasificar")
    result = runtime.ask("Describe la utilidad de una herramienta de versiones.")
    assert isinstance(result, LLMResponse)
    assert events == ["classifier_llm", "policy", "candidate"]
    assert runtime.questions_asked == 1 and len(candidate.requests) == 1
    system = candidate.requests[0][0]["content"]
    assert "CLASIFICACION_DESCRIPTIVA_JSON" in system
    assert "JUSTIFICACION_LIBRE_NO_AUTORIZADA" not in system
    assert runtime.session_dict()["interventions"][0]["classification"]["result"]["method"] == "llm"
    record = roundtrip(runtime, tmp_path)
    assert record["session_version"] == "1.2.0"
    assert record["interventions"][0]["candidate_question_number"] == 1
    assert record["interventions"][0]["policy"]["action"] == "responder"


@pytest.mark.parametrize("classifier_version", ["1.0.0", "1.1.0", "1.2.0", "1.2.1", "1.2.2", "1.2.3", "1.3.0", "1.4.0", "1.4.1", "1.4.2", "1.5.0"])
def test_session_reader_accepts_old_and_new_llm_protocol_versions(classifier_version, tmp_path):
    runtime, _, _ = make_runtime()
    runtime.ask("Describe la utilidad de una herramienta de versiones.")
    runtime.close()
    record = runtime.session_dict()
    trace = record["interventions"][0]["classification"]["trace"]["llm"]
    trace["classifier_version"] = classifier_version
    if classifier_version != "1.5.0":
        trace.pop("few_shot")
    if classifier_version == "1.3.0":
        trace.update(llm_contract_version="1.2.0", aggregation_version="1.0.0")
    elif classifier_version not in {"1.4.0", "1.4.1", "1.4.2", "1.5.0"}:
        for key in ("llm_contract_version", "aggregation_version", "aggregation_applied"):
            trace.pop(key)
    assert load_session(save_session(record, tmp_path))["interventions"][0]["classification"]["result"]["contract_version"] == "1.0.0"


@pytest.mark.parametrize("field", ["llm_contract_version", "aggregation_version", "aggregation_applied"])
@pytest.mark.parametrize("mutation", ["missing", "false_claim"])
def test_new_session_requires_valid_host_owned_derivation_provenance(field, mutation, tmp_path):
    runtime, _, _ = make_runtime()
    runtime.ask("Describe la utilidad de una herramienta de versiones.")
    runtime.close()
    record = runtime.session_dict()
    trace = record["interventions"][0]["classification"]["trace"]["llm"]
    assert trace["llm_contract_version"] == "1.3.0"
    assert trace["aggregation_version"] == "1.1.0"
    assert trace["aggregation_applied"] is True
    if mutation == "missing":
        trace.pop(field)
    else:
        trace[field] = False if field == "aggregation_applied" else "0.0.0"
    with pytest.raises(SessionLogError):
        save_session(record, tmp_path)


@pytest.mark.parametrize("text", ["Hola", "Gracias por tu respuesta", "", "   ", "¿Qué ocurrió después?"])
def test_non_sent_interventions_are_logged_without_counting_or_entering_candidate_history(text, tmp_path):
    runtime, semantic, candidate = make_runtime()
    notice = runtime.ask(text)
    assert isinstance(notice, ResponsePolicyDecision)
    assert runtime.questions_asked == 0 and runtime.history_messages() == []
    assert candidate.requests == semantic.requests == []
    record = roundtrip(runtime, tmp_path)
    assert len(record["interventions"]) == 1 and record["attempts"] == []
    assert record["interventions"][0]["status"] == "handled"
    assert record["interventions"][0]["candidate_question_number"] is None


@pytest.mark.parametrize("mode", ["ambiguous", "invalid", "provider_error"])
def test_ambiguity_and_technical_failure_have_distinct_notices_and_no_candidate_call(mode, tmp_path):
    runtime, semantic, candidate = make_runtime(semantic=SemanticClient(mode=mode))
    result = runtime.ask("Explica tu actuación en esa situación.")
    assert result.action == ("aclarar" if mode == "ambiguous" else "error_tecnico")
    assert runtime.questions_asked == 0 and candidate.requests == []
    assert len(semantic.requests) == (2 if mode == "invalid" else 1)
    record = roundtrip(runtime, tmp_path)
    serialized = json.dumps(record)
    assert "SALIDA_PRIVADA_INVALIDA" not in serialized and "CUERPO_PRIVADO_NO_REGISTRAR" not in serialized
    technical = record["interventions"][0]["classification"]["result"]["technical_error"]
    assert (technical is None) == (mode == "ambiguous")


def test_context_is_recent_completed_pairs_only_with_literal_prefixes_and_same_session(tmp_path):
    long_answer = "La coordinadora detectó solicitudes ausentes. " + "detalle " * 400
    candidate = CandidateClient(outcomes=[answer(long_answer), LLMTimeoutError("Fallo simulado"), answer(long_answer)])
    runtime, semantic, _ = make_runtime(semantic=SemanticClient(mode="followup"), candidate=candidate)
    runtime.ask("¿Conoces SQL?")
    with pytest.raises(LLMTimeoutError):
        runtime.ask("¿Conoces Git?")
    runtime.ask("¿Has usado Python?")
    assert [a["status"] for a in runtime.session_dict()["attempts"]] == ["completed", "error", "completed"]
    runtime.ask("¿Qué hiciste después?")
    context = semantic.requests[-1]["context_turns"]
    assert [turn["turn_number"] for turn in context] == [1, 3]
    assert all(len(message["content"]) <= 1200 for turn in context for message in turn["messages"])
    assert context[0]["messages"][1]["content"] == long_answer[:1200]
    assert runtime.history_messages()[1]["content"] == long_answer
    record = roundtrip(runtime, tmp_path)
    assert record["interventions"][-1]["available_context_turn_ids"] == [1, 3]
    assert record["interventions"][-1]["classification"]["result"]["context_turn_ids"] == [3]
    another, other_semantic, _ = make_runtime()
    another.ask("Describe una herramienta de versiones.")
    assert other_semantic.requests[0]["context_turns"] == []


def test_context_selector_keeps_at_most_two_completed_pairs():
    attempts = [{"question_number": n, "question": "Pregunta", "status": "completed",
                 "response": {"text": "Respuesta"}} for n in range(1, 6)]
    assert [turn["turn_number"] for turn in select_classification_context(attempts)] == [4, 5]
    spaced = " " * 1500 + "Texto de contexto."
    attempts[-1].update(question=spaced, response={"text": spaced})
    fragments = select_classification_context(attempts)[-1]["messages"]
    assert all(message["content"] == "Texto de contexto." for message in fragments)
    assert attempts[-1]["question"] == spaced


def test_twenty_candidate_attempts_include_failures_but_not_notices(tmp_path):
    outcomes = [LLMTimeoutError("Fallo simulado")] + [answer()] * 19
    runtime, semantic, candidate = make_runtime(candidate=CandidateClient(outcomes=outcomes))
    for _ in range(3):
        runtime.ask("Hola")
    for n in range(20):
        if n == 0:
            with pytest.raises(LLMTimeoutError):
                runtime.ask("¿Conoces Git?")
        else:
            runtime.ask("¿Conoces Git?")
    assert runtime.finished and runtime.questions_asked == len(candidate.requests) == 20
    assert semantic.requests == []
    with pytest.raises(InterviewFinishedError):
        runtime.ask("Hola")
    record = roundtrip(runtime, tmp_path)
    assert len(record["interventions"]) == 23 and len(record["attempts"]) == 20
    assert record["close_reason"] == "question_limit"


@pytest.mark.parametrize("where", ["classifier", "candidate"])
def test_interruption_is_recorded_without_losing_attempt_count_or_history(where, tmp_path):
    semantic = SemanticClient(mode="interrupt" if where == "classifier" else "valid")
    candidate = CandidateClient(outcomes=[KeyboardInterrupt()])
    runtime, _, _ = make_runtime(semantic=semantic, candidate=candidate)
    with pytest.raises(KeyboardInterrupt):
        runtime.ask("Describe una herramienta de versiones.")
    runtime.close("interrupted")
    record = roundtrip(runtime, tmp_path)
    assert len(record["attempts"]) == (0 if where == "classifier" else 1)
    assert record["interventions"][0]["status"] == "interrupted"
    assert runtime.history_messages() == []


def test_profile_integrity_is_checked_after_classification_before_candidate(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = tmp_path / "candidate.json"
    original_bytes = (root / "data/candidates/candidato_junior.json").read_bytes()
    source.write_bytes(original_bytes)
    setup = load_interview_setup(candidate_path=source)
    semantic = SemanticClient(callback=lambda data: source.write_bytes(original_bytes + b"\n"))
    runtime, _, candidate = make_runtime(semantic=semantic, setup=setup)
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("Describe una herramienta de versiones.")
    assert candidate.requests == [] and runtime.questions_asked == 0
    record = roundtrip(runtime, tmp_path)
    assert record["source_integrity"] == "failed" and record["close_reason"] == "profile_integrity_error"
    assert record["interventions"][0]["issues"][0]["code"] == "profile_integrity_error"
    assert (root / "data/candidates/candidato_junior.json").read_bytes() == original_bytes


def test_classification_and_extractive_candidate_memory_coexist_and_save(tmp_path):
    runtime, semantic, candidate = make_runtime(context_policy=LiveContextPolicy(trigger_input_tokens=1))
    for _ in range(4):
        runtime.ask("¿Conoces Git?")
    assert semantic.requests == [] and candidate.selections == 1
    record = roundtrip(runtime, tmp_path)
    assert record["session_version"] == "1.2.0" and len(record["context_events"]) == 4
    assert len(record["interventions"]) == len(record["attempts"]) == 4
    sent = [messages for messages in candidate.requests if messages[0]["content"] != SELECTION_INSTRUCTIONS]
    assert all("CLASIFICACION_DESCRIPTIVA_JSON" in messages[0]["content"] for messages in sent)
    for event, messages in zip(record["context_events"], sent):
        encoded = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        assert event["preparation"]["messages_sha256"] == hashlib.sha256(encoded).hexdigest().upper()


def test_clear_compound_without_a_principal_is_answered_once_not_mistaken_for_uncertainty(tmp_path):
    class CompoundClient(SemanticClient):
        def generate(self, messages):
            data = json.loads(messages[1]["content"])["input"]
            self.requests.append(deepcopy(data))
            first, second = "¿Conoces Git?", "¿Qué harías si una entrega fallara?"
            result = annotation(data)
            result["classification"].update(main_approach=None, main_form=None)
            u1 = deepcopy(result["units"][0])
            u1.update(quote=first)
            u1["classification"].update(forms=["cerrada"], main_form="cerrada")
            u2 = deepcopy(result["units"][0])
            u2.update(unit_id="u2", quote=second)
            u2["classification"].update(approaches=["situacional"], main_approach="situacional")
            result["units"] = [u1, u2]
            return answer(json.dumps(to_wire(result)))
    runtime, semantic, candidate = make_runtime(semantic=CompoundClient())
    result = runtime.ask("¿Conoces Git? ¿Qué harías si una entrega fallara?")
    assert isinstance(result, LLMResponse) and len(candidate.requests) == 1
    record = roundtrip(runtime, tmp_path)
    assert record["interventions"][0]["policy"]["action"] == "responder"
    assert record["interventions"][0]["classification"]["result"]["classification"]["main_approach"] is None


def test_incomplete_candidate_response_counts_and_is_not_promoted_to_history(tmp_path):
    from harness.llm.client import LLMInvalidResponseError
    incomplete = LLMResponse("Respuesta cortada", "modelo", "ollama", 0.1, finish_reason="length")
    runtime, _, _ = make_runtime(candidate=CandidateClient(outcomes=[incomplete]))
    with pytest.raises(LLMInvalidResponseError):
        runtime.ask("¿Conoces Git?")
    record = roundtrip(runtime, tmp_path)
    assert runtime.questions_asked == 1 and runtime.history_messages() == []
    assert record["interventions"][0]["status"] == record["attempts"][0]["status"] == "incomplete"


def test_forged_validated_result_is_rejected_before_candidate_and_not_logged_as_accepted(tmp_path):
    from harness.hybrid_question_classifier import HybridClassification
    class ForgedClassifier(HybridQuestionClassifier):
        def classify(self, text, **kwargs):
            report = super().classify(text, **kwargs)
            result = report.result
            result["intervention_id"] = "IDENTIDAD_FALSA_NO_CONFIABLE"
            return HybridClassification(report.route, json.dumps(result), json.dumps(report.trace))
    candidate = CandidateClient()
    classifier = ForgedClassifier(LLMQuestionClassifier(SemanticClient()))
    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), candidate, classifier=classifier)
    with pytest.raises(ValueError):
        runtime.ask("¿Conoces Git?")
    assert not candidate.requests and runtime.questions_asked == 0
    record = roundtrip(runtime, tmp_path)
    assert record["interventions"][0]["classification"] is None
    assert "IDENTIDAD_FALSA_NO_CONFIABLE" not in json.dumps(record)


@pytest.mark.parametrize("mutation", ["error_code", "terminal_code", "status", "third_attempt"])
def test_llm_audit_rejects_inconsistent_error_metadata(mutation, tmp_path):
    runtime, _, _ = make_runtime(semantic=SemanticClient(mode="invalid"))
    runtime.ask("Describe una herramienta de versiones.")
    runtime.close()
    record = runtime.session_dict()
    report = record["interventions"][0]["classification"]
    if mutation == "error_code":
        report["trace"]["llm"]["attempts"][0]["error_code"] = "authentication_error"
    elif mutation == "terminal_code":
        report["result"]["technical_error"] = "contrato_invalido"
    elif mutation == "status":
        report["trace"]["llm"]["status"] = "clasificada"
    else:
        report["trace"]["llm"]["attempts"].append(deepcopy(report["trace"]["llm"]["attempts"][-1]))
    with pytest.raises(SessionLogError):
        save_session(record, tmp_path / "invalid")


@pytest.mark.parametrize("memory", [False, True])
def test_legacy_sessions_still_save_and_load_without_new_fields(memory, tmp_path):
    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), CandidateClient(),
                               context_policy=LiveContextPolicy() if memory else None)
    runtime.ask("Pregunta tradicional")
    record = roundtrip(runtime, tmp_path)
    assert record["session_version"] == ("1.1.0" if memory else "1.0.0")
    assert "interventions" not in record and "classification_policy" not in record


@pytest.mark.parametrize("mutation", ["identity", "policy", "counter", "source", "trace", "context", "unknown_field"])
def test_saved_records_reject_inconsistent_classification_policy_or_sources(mutation, tmp_path):
    runtime, _, _ = make_runtime()
    runtime.ask("¿Conoces Git?")
    runtime.close()
    record = runtime.session_dict()
    event = record["interventions"][0]
    if mutation == "identity":
        event["classification"]["result"]["intervention_id"] = "otro"
    elif mutation == "policy":
        event["policy"]["action"] = "aclarar"
    elif mutation == "counter":
        event["candidate_question_number"] = None
    elif mutation == "source":
        event["text"] = "Pregunta cambiada"
    elif mutation == "trace":
        event["classification"]["trace"]["local"]["status"] = "abstencion"
    elif mutation == "context":
        event["available_context_turn_ids"] = [99]
    else:
        event["classification"]["trace"]["local"]["api_key"] = "DATO_NO_PERMITIDO"
    with pytest.raises(SessionLogError):
        save_session(record, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_cli_classification_mode_saves_notices_and_closes_both_clients(monkeypatch, tmp_path, capsys):
    from harness import session_log
    candidate_calls, classification_calls = [], []
    def candidate_handler(request):
        candidate_calls.append(request)
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": "Respuesta simulada."}})
    def classification_handler(request):
        classification_calls.append(request)
        pytest.fail("Las entradas simples de esta prueba deben ser locales")
    candidate = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(candidate_handler))
    semantic = create_classification_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(classification_handler))
    monkeypatch.setattr(run_interview, "create_client", lambda: candidate)
    monkeypatch.setattr(run_interview, "create_classification_client", lambda **kwargs: semantic)
    entries = iter(["/cv", "/iniciar", "Hola", "  ", "¿Qué pasó después?", "¿Has usado Git?", "/sesion", "/salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main(["--classify"]) == 0
    record = load_session(next(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json")))
    assert len(record["interventions"]) == 4 and len(record["attempts"]) == 1
    assert len(candidate_calls) == 1 and classification_calls == []
    assert candidate._http.is_closed and semantic._http.is_closed
    output = capsys.readouterr().out
    assert "Simulador:" in output and "RESPUESTA DEL CANDIDATO | PREGUNTA 01/20" in output
    assert "Respuesta simulada." in output
    assert "Preguntas enviadas: 1/20" in output and "Intervenciones registradas: 4" in output


def test_main_launcher_enables_classification_without_putting_credentials_in_command(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(start_interview, "load_json", lambda path: {
        "local_model": "gemma4:e4b", "api_model": "gemma4:26b", "api_key": "CLAVE_FICTICIA_NO_REAL"})
    monkeypatch.setattr("builtins.input", lambda _: "1")
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(start_interview.subprocess, "run", run)
    assert start_interview.main() == 0
    assert "--classify" in calls[0] and "--extractive-context" in calls[0]
    assert "CLAVE_FICTICIA_NO_REAL" not in " ".join(calls[0])


def test_unab_cli_separates_classifier_and_candidate_usage_without_exposing_credentials(monkeypatch, capsys):
    from harness import session_log
    env = {"LLM_PROVIDER": "unab", "LLM_ALLOW_EXTERNAL_API": "true", "UNAB_MODEL": "gemma4:26b",
           "UNAB_API_KEY": "CLAVE_FICTICIA_SOLO_TEST"}
    clients = []
    def envelope(content):
        return {"model": "gemma4:26b", "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}}
    def candidate_handler(request):
        return httpx.Response(200, json=envelope("Respuesta simulada del candidato."))
    def classification_handler(request):
        data = json.loads(request.content)["messages"][1]["content"]
        result = annotation(json.loads(data)["input"])
        return httpx.Response(200, json=envelope(json.dumps(result)))
    candidate = create_client(env, transport=httpx.MockTransport(candidate_handler))
    def classifier_factory(**kwargs):
        client = create_classification_client(env, transport=httpx.MockTransport(classification_handler), **kwargs)
        clients.append(client)
        return client
    monkeypatch.setattr(run_interview, "create_client", lambda: candidate)
    monkeypatch.setattr(run_interview, "create_classification_client", classifier_factory)
    entries = iter(["/iniciar", "Describe una herramienta de versiones.", "/salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main(["--classify", "--classifier-max-output-tokens", "1024"]) == 0
    record = load_session(next(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json")))
    assert record["classification_policy"]["max_output_tokens"] == 1024
    assert candidate.settings.max_output_tokens == 2048 and clients[0].settings.max_output_tokens == 1024
    results = session_log.DEFAULT_SESSIONS_DIR.parent / "results"
    files = [results / f"unab-usage-{record['session_id']}.json", results / f"unab-classifier-usage-{record['session_id']}.json"]
    assert all(path.exists() for path in files)
    output = capsys.readouterr().out + json.dumps(record) + "".join(path.read_text(encoding="utf-8") for path in files)
    assert "CLAVE_FICTICIA_SOLO_TEST" not in output
    assert all(len(json.loads(path.read_text(encoding="utf-8"))["calls"]) == 1 for path in files)
    assert candidate._http.is_closed and clients[0]._http.is_closed

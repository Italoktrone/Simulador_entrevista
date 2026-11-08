"""Flujo, presentación y persistencia sin consultar modelos reales."""

import json

import pytest

from harness.application.cli import run_console
from harness.interview_config import load_interview_setup
from harness.question_evaluator import QuestionEvaluator
from harness.runtime import InterviewRuntime
from harness.prompt_builder import load_instructions
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.llm_question_classifier import LLMQuestionClassifier
from harness.llm.client import LLMTimeoutError
from harness.session_log import save_session, load_session, SessionLogError
from tests.evaluation_fixtures import EvaluationClient
from tests.integration.test_pre_response_classification import SemanticClient, CandidateClient


def make_runtime(*, semantic=None, candidate=None, evaluation=None, context_policy=None):
    return InterviewRuntime(load_interview_setup(), load_instructions(), candidate or CandidateClient(),
                            classifier=HybridQuestionClassifier(LLMQuestionClassifier(semantic or SemanticClient())),
                            evaluator=QuestionEvaluator(evaluation or EvaluationClient()), context_policy=context_policy)


def roundtrip(runtime, directory):
    runtime.close()
    return load_session(save_session(runtime.session_dict(), directory))


def test_evaluation_uses_pre_turn_snapshot_and_keeps_feedback_out_of_candidate_history(tmp_path):
    client = EvaluationClient()
    candidate = CandidateClient()
    runtime = make_runtime(evaluation=client, candidate=candidate)
    runtime.ask("¿Has utilizado Git?")
    first = runtime.last_evaluation
    assert first["request"]["context_turns"] == []
    runtime.ask("¿Has utilizado Python?")
    last = runtime.last_evaluation
    assert [t["turn_number"] for t in last["request"]["context_turns"]] == [1]
    assert "Retroalimentación" not in json.dumps(candidate.requests)
    assert runtime.questions_asked == 2
    assert roundtrip(runtime, tmp_path)["evaluations"] == runtime.session_dict()["evaluations"]


@pytest.mark.parametrize("text,mode,status", [("Hola", "valid", "no_evaluable"), ("¿Qué pasó después?", "valid", "no_ejecutada"),
    ("Describe una solución para un error complejo.", "invalid", "no_ejecutada"), ("", "valid", "no_evaluable")])
def test_policy_branches_do_not_call_candidate_or_evaluator(text, mode, status, tmp_path):
    candidate, evaluation = CandidateClient(), EvaluationClient()
    runtime = make_runtime(semantic=SemanticClient(mode=mode), candidate=candidate, evaluation=evaluation)
    runtime.ask(text)
    assert not candidate.requests and not evaluation.requests and runtime.questions_asked == 0
    assert runtime.last_evaluation["status"] == status
    roundtrip(runtime, tmp_path)


def test_failed_evaluation_preserves_answer_and_allows_next_question(tmp_path):
    evaluation = EvaluationClient([LLMTimeoutError("ERROR_PRIVADO")])
    runtime = make_runtime(evaluation=evaluation)
    response = runtime.ask("¿Has utilizado Git?")
    assert response.text and runtime.last_evaluation["status"] == "no_disponible"
    runtime.ask("¿Has utilizado Python?")
    assert runtime.last_evaluation["status"] == "evaluada"
    assert "ERROR_PRIVADO" not in json.dumps(roundtrip(runtime, tmp_path))


def test_candidate_failure_does_not_call_evaluator(tmp_path):
    evaluation = EvaluationClient()
    runtime = make_runtime(candidate=CandidateClient(outcomes=[LLMTimeoutError("fallo")]), evaluation=evaluation)
    with pytest.raises(LLMTimeoutError):
        runtime.ask("¿Has utilizado Git?")
    assert evaluation.requests == [] and runtime.last_evaluation["status"] == "no_ejecutada"
    roundtrip(runtime, tmp_path)


def test_twentieth_answer_is_evaluated_before_session_is_saved(tmp_path):
    runtime = make_runtime()
    for _ in range(20):
        runtime.ask("¿Has utilizado Git?")
    data = roundtrip(runtime, tmp_path)
    assert runtime.finished and data["close_reason"] == "question_limit"
    assert len(data["evaluations"]) == 20 and data["evaluations"][-1]["status"] == "evaluada"


def test_console_displays_candidate_before_evaluation_and_feedback_before_next_input():
    events = []
    evaluation = EvaluationClient(events=events)
    runtime = make_runtime(evaluation=evaluation)
    inputs = iter(["/iniciar", "¿Has utilizado Git?", "/salir"])
    def read(prompt):
        events.append(prompt)
        return next(inputs)
    run_console(runtime, provider="ollama", model="modelo", input_fn=read, output_fn=events.append)
    candidate = next(i for i, e in enumerate(events) if "RESPUESTA DEL CANDIDATO | PREGUNTA 01/20" in e)
    feedback = next(i for i, e in enumerate(events) if "EVALUACIÓN DE LA PREGUNTA 01 | PROVISIONAL" in e)
    next_input = events.index("Pregunta 2/20> ")
    assert candidate < events.index("evaluation") < feedback < next_input


@pytest.mark.parametrize("mutation", ["context", "score", "identity", "classification", "missing"])
def test_tampered_evaluation_is_rejected_at_save(mutation, tmp_path):
    runtime = make_runtime()
    runtime.ask("¿Has utilizado Git?")
    runtime.close()
    data = runtime.session_dict()
    record = data["evaluations"][0]
    if mutation == "context":
        record["request"]["context_turns"] = [{"turn_number": 1, "question": "¿Has utilizado Git?", "answer": "Respuesta actual", "truncated": False}]
    elif mutation == "score":
        record["normalized_score"] = 100
    elif mutation == "identity":
        record["question_number"] = 2
    elif mutation == "classification":
        record["request"]["classification"] = None
    else:
        data["evaluations"] = []
    with pytest.raises(SessionLogError):
        save_session(data, tmp_path)


def test_unexpected_evaluator_error_does_not_destroy_candidate_turn(monkeypatch, tmp_path):
    runtime = make_runtime()
    def broken(*args, **kwargs):
        raise RuntimeError("ERROR_INTERNO_PRIVADO")
    monkeypatch.setattr(runtime._evaluator, "evaluate", broken)
    assert runtime.ask("¿Has utilizado Git?").text
    assert runtime.last_evaluation["reason_code"] == "error_evaluador"
    assert "ERROR_INTERNO_PRIVADO" not in json.dumps(roundtrip(runtime, tmp_path))


def test_memory_selection_classification_and_evaluation_coexist(tmp_path):
    from harness.live_context import LiveContextPolicy
    runtime = make_runtime(context_policy=LiveContextPolicy(trigger_input_tokens=1))
    for _ in range(4):
        runtime.ask("¿Has utilizado Git?")
    data = roundtrip(runtime, tmp_path)
    assert data["session_version"] == "1.3.0"
    assert len(data["context_events"]) == len(data["evaluations"]) == 4
    assert [t["turn_number"] for t in data["evaluations"][-1]["request"]["context_turns"]] == [1, 2, 3]


@pytest.mark.parametrize("stage", ["classifier", "candidate", "evaluation"])
def test_interruption_keeps_session_savable(stage, tmp_path):
    runtime = make_runtime(
        semantic=SemanticClient(mode="interrupt") if stage == "classifier" else None,
        candidate=CandidateClient(outcomes=[KeyboardInterrupt()]) if stage == "candidate" else None,
        evaluation=EvaluationClient([KeyboardInterrupt()]) if stage == "evaluation" else None)
    text = "Describe una dificultad técnica." if stage == "classifier" else "¿Has utilizado Git?"
    with pytest.raises(KeyboardInterrupt):
        runtime.ask(text)
    runtime.close("interrupted")
    data = roundtrip(runtime, tmp_path)
    assert data["evaluations"][0]["status"] == "no_ejecutada"
    assert bool(data["attempts"] and data["attempts"][-1]["status"] == "completed") == (stage == "evaluation")


def test_run_entrypoint_activates_evaluator_and_persists(monkeypatch, tmp_path):
    from harness.llm.config import OllamaSettings
    from scripts import run_interview
    from contextlib import nullcontext
    from harness import session_log
    candidate, semantic, evaluation = CandidateClient(), SemanticClient(), EvaluationClient()
    for client in (candidate, semantic, evaluation):
        client.provider = "ollama"
        client.settings = OllamaSettings(model="modelo-simulado")
    monkeypatch.setattr(run_interview, "create_client", lambda: nullcontext(candidate))
    monkeypatch.setattr(run_interview, "create_classification_client", lambda **kwargs: nullcontext(semantic))
    monkeypatch.setattr(run_interview, "create_evaluation_client", lambda **kwargs: nullcontext(evaluation))
    monkeypatch.setattr(session_log, "DEFAULT_SESSIONS_DIR", tmp_path)
    lines = iter(["/iniciar", "¿Has utilizado Git?", "/salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(lines))
    assert run_interview.main(["--evaluate"]) == 0
    result = load_session(next(tmp_path.glob("session-*.json")))
    assert result["session_version"] == "1.3.0" and result["evaluations"][0]["status"] == "evaluada"


def test_selector_forwards_optional_evaluation_flag(monkeypatch):
    from scripts import start_interview
    from types import SimpleNamespace
    monkeypatch.setattr(start_interview, "load_json", lambda _: {"local_model": "modelo-local", "api_model": "modelo-api", "api_key": ""})
    monkeypatch.setattr("builtins.input", lambda _: "1")
    commands = []
    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(start_interview.subprocess, "run", run)
    assert start_interview.main(["--evaluate"]) == 0
    assert "--evaluate" in commands[0]


def test_summary_counts_technical_evaluation_failure_separately():
    from harness.application.cli import format_session
    runtime = make_runtime(evaluation=EvaluationClient([LLMTimeoutError("privado")]))
    runtime.ask("¿Has utilizado Git?")
    summary = format_session(runtime)
    assert "Incidencias técnicas: 1" in summary
    assert "Fallos técnicos del evaluador: 1" in summary
    assert "Respuestas completas: 1" in summary

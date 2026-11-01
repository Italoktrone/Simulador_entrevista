"""Política, contador y auditoría con selección simulada, sin red."""

from copy import deepcopy
import json

import pytest

from harness.application.cli import format_session
from harness.history_summary import SELECTION_INSTRUCTIONS
from harness.interview_config import load_interview_setup
from harness.live_context import LiveContextPolicy
from harness.llm.client import LLMContextLimitError, LLMResponse, LLMTimeoutError
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import SessionLogError, load_session, save_session
from harness.summary_context import EXTRACT_MARKER


FILLER = "Esta explicación general introduce el tema de la conversación y desarrolla una presentación extensa de la respuesta. " * 12


class Client:
    def __init__(self, candidates=None, selection="valid", action=None):
        self.candidates = iter(candidates or ["Elegí Inventario Aula. " + FILLER + "No tuvo clientes comerciales.", "Elegí pytest.", "Primero Inventario Aula.", "Respuesta posterior."])
        self.selection = selection
        self.action = action
        self.requests = []
        self.candidate_calls = 0
        self.selector_calls = 0
        self.input_tokens = 100

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        if messages[0]["content"] == SELECTION_INSTRUCTIONS:
            self.selector_calls += 1
            if self.action:
                self.action()
            if isinstance(self.selection, BaseException):
                raise self.selection
            source = json.loads(messages[1]["content"])
            text = json.dumps({"selections": [{"question_number": t["question_number"], "segment_indices": t["required_segment_indices"]} for t in source["old_turns"]]}) if self.selection == "valid" else "TEXTO_RESERVADO"
            return LLMResponse(text, "selector-simulado", "ollama", 0.1, input_tokens=50, finish_reason="stop")
        self.candidate_calls += 1
        value = next(self.candidates)
        if isinstance(value, BaseException):
            raise value
        return LLMResponse(value, "candidato-simulado", "ollama", 0.2, input_tokens=self.input_tokens, finish_reason="stop")


def runtime_for(client=None, *, setup=None, trigger=1):
    policy = LiveContextPolicy(minimum_completed_pairs=2, keep_recent_pairs=1, trigger_input_tokens=trigger)
    return InterviewRuntime(setup or load_interview_setup(), load_instructions(), client or Client(),
                            provider="ollama", model="solicitado", context_policy=policy)


def first_two(runtime):
    runtime.ask("Primer proyecto")
    runtime.ask("Herramienta")


def test_policy_default_budget_unknown_metrics_and_explicit_trigger():
    policy = LiveContextPolicy()
    assert policy.trigger_input_tokens == 7424
    assert policy.keep_recent_pairs == 2 and policy.minimum_completed_pairs == 3
    for count, reason in [(None, "below_threshold"), (0, "below_threshold"), (7423, "below_threshold"), (7424, "reported_input_tokens")]:
        session = {"attempts": [{"status": "completed", "response": {"input_tokens": count}, "issues": []}] * 3}
        assert policy.reason(session, False) == reason
        assert policy.reason(session, True) == "already_active"


@pytest.mark.parametrize("changes", [
    {"trigger_input_tokens": 0}, {"trigger_input_tokens": True}, {"trigger_input_tokens": 7425},
    {"minimum_completed_pairs": 2, "keep_recent_pairs": 2},
    {"minimum_completed_pairs": 20}, {"keep_recent_pairs": 0}, {"context_size": 512},
])
def test_invalid_policy_is_rejected(changes):
    with pytest.raises(ValueError):
        LiveContextPolicy(**changes)


def test_live_selection_is_not_a_question_and_uses_original_history_each_time(tmp_path):
    client = Client()
    runtime = runtime_for(client)
    first_two(runtime)
    client.input_tokens = 0
    runtime.ask("¿Cuál mencionaste primero?")
    runtime.ask("Otra pregunta")
    runtime.close("user_exit")
    snapshot = runtime.session_dict()
    assert runtime.questions_asked == client.candidate_calls == 4 and client.selector_calls == 2
    assert snapshot["session_version"] == "1.1.0"
    assert [e["trigger_reason"] for e in snapshot["context_events"]] == ["insufficient_history", "insufficient_history", "reported_input_tokens", "already_active"]
    assert snapshot["context_events"][2]["preparation"]["mode"] == "extractive_summary"
    assert client.requests[3][2]["content"].startswith(EXTRACT_MARKER)
    selector_requests = [r for r in client.requests if r[0]["content"] == SELECTION_INSTRUCTIONS]
    assert all("Esta explicación general" in r[1]["content"] for r in selector_requests)
    assert all(EXTRACT_MARKER not in r[1]["content"] for r in selector_requests)
    assert "Esta explicación general" in runtime.history_messages()[1]["content"]
    assert "context_events" not in str(client.requests) and "selector_metrics" not in str(client.requests)
    assert load_session(save_session(snapshot, tmp_path)) == snapshot
    snapshot["context_events"][0]["preparation"]["mode"] = "cambio"
    assert runtime.session_dict()["context_events"][0]["preparation"]["mode"] == "full_history"


@pytest.mark.parametrize("selection, code", [("invalid", "summary_selection_error"), (LLMTimeoutError("TEXTO_RESERVADO"), "timeout")])
def test_failed_selector_falls_back_once_and_records_safe_incident(tmp_path, selection, code):
    client = Client(selection=selection)
    runtime = runtime_for(client)
    first_two(runtime)
    runtime.ask("Tercera pregunta")
    runtime.close()
    snapshot = runtime.session_dict()
    event = snapshot["context_events"][-1]
    assert runtime.questions_asked == 3 and client.candidate_calls == 3 and client.selector_calls == 1
    assert event["selector_status"] == "failed" and event["issues"][0]["code"] == code
    assert event["preparation"]["mode"] == "full_history" and event["preparation"]["reason"] == "selector_failed"
    assert event["summary_selections"] is None and event["selector_metrics"] is None
    assert "Esta explicación general" in client.requests[-1][2]["content"]
    assert "TEXTO_RESERVADO" not in json.dumps(snapshot)
    assert "Incidencias técnicas: 1" in format_session(runtime)
    assert load_session(save_session(snapshot, tmp_path)) == snapshot


def test_context_limit_in_previous_attempt_can_activate_policy_without_retrying_that_question(tmp_path):
    client = Client(candidates=["Inventario Aula.", "pytest.", LLMContextLimitError("Límite"), "Respuesta cuarta."])
    runtime = runtime_for(client, trigger=7424)
    first_two(runtime)
    with pytest.raises(LLMContextLimitError):
        runtime.ask("Pregunta extensa")
    assert client.selector_calls == 0 and runtime.questions_asked == 3
    runtime.ask("Pregunta menor")
    runtime.close()
    record = runtime.session_dict()
    assert record["context_events"][-1]["trigger_reason"] == "previous_context_limit"
    assert [a["status"] for a in record["attempts"]] == ["completed", "completed", "error", "completed"]
    assert client.candidate_calls == 4 and client.selector_calls == 1
    assert load_session(save_session(record, tmp_path)) == record


def test_interrupted_selection_has_no_candidate_attempt_and_programmatic_caller_can_continue(tmp_path):
    client = Client(selection=KeyboardInterrupt())
    runtime = runtime_for(client)
    first_two(runtime)
    with pytest.raises(KeyboardInterrupt):
        runtime.ask("Tercera")
    assert runtime.questions_asked == 2 and client.candidate_calls == 2
    assert runtime.session_dict()["context_events"][-1]["candidate_sent"] is False
    client.selection = "valid"
    runtime.ask("Tercera reformulada")
    runtime.close("user_exit")
    record = runtime.session_dict()
    assert [e["before_question_number"] for e in record["context_events"]] == [1, 2, 3, 3]
    assert load_session(save_session(record, tmp_path)) == record


@pytest.mark.parametrize("provider_also_fails", [False, True])
def test_profile_change_during_selector_aborts_before_sending_candidate(tmp_path, provider_also_fails):
    original = load_interview_setup()
    path = tmp_path / "candidate.json"
    path.write_bytes(original.candidate.source_path.read_bytes())
    setup = load_interview_setup(candidate_path=path)
    client = Client(selection=LLMTimeoutError("TEXTO_RESERVADO") if provider_also_fails else "valid", action=lambda: path.write_bytes(path.read_bytes() + b"\n"))
    runtime = runtime_for(client, setup=setup)
    first_two(runtime)
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("Tercera")
    record = runtime.session_dict()
    assert record["source_integrity"] == "failed" and record["status"] == "closed"
    assert runtime.questions_asked == client.candidate_calls == 2
    assert record["context_events"][-1]["selector_status"] == "aborted"
    assert record["context_events"][-1]["candidate_sent"] is False
    assert load_session(save_session(record, tmp_path / "logs")) == record
    assert "TEXTO_RESERVADO" not in json.dumps(record)


def test_last_candidate_question_closes_limit_without_counting_selector(tmp_path):
    setup = load_interview_setup()
    config = tmp_path / "config.json"
    config.write_text(json.dumps(setup.config_dict() | {"max_questions": 3}), encoding="utf-8")
    runtime = runtime_for(setup=load_interview_setup(config_path=config))
    first_two(runtime)
    runtime.ask("Última")
    record = runtime.session_dict()
    assert runtime.questions_asked == 3 and record["close_reason"] == "question_limit"
    assert len(record["context_events"]) == 3
    assert load_session(save_session(record, tmp_path / "logs")) == record


@pytest.fixture
def closed_record():
    runtime = runtime_for()
    first_two(runtime)
    runtime.ask("Tercera")
    runtime.close("user_exit")
    return runtime.session_dict()


@pytest.mark.parametrize("path,value", [
    (("session_version",), "1.0.0"),
    (("context_policy", "trigger_input_tokens"), 0),
    (("context_policy", "keep_recent_pairs"), 2),
    (("context_events", 0, "event_number"), 2),
    (("context_events", 0, "before_question_number"), 2),
    (("context_events", 0, "recorded_at"), "2026-10-31T12:00:00-03:00"),
    (("context_events", 0, "preparation_elapsed_seconds"), -1),
    (("context_events", 0, "candidate_sent"), False),
    (("context_events", 2, "trigger_reason"), "below_threshold"),
    (("context_events", 2, "preparation", "saved_message_bytes"), 99999),
    (("context_events", 2, "preparation", "messages_sha256"), "huella inválida"),
    (("context_events", 2, "preparation", "source_history_sha256"), "0" * 64),
    (("context_events", 2, "selector_status"), "not_requested"),
    (("context_events", 2, "summary_selections", 0, "segment_indices"), [999]),
    (("context_events", 2, "selector_metrics", "text"), "TEXTO_RESERVADO"),
])
def test_invalid_audit_is_rejected_before_creating_directory(closed_record, tmp_path, path, value):
    target = closed_record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    output = tmp_path / "not-created"
    with pytest.raises(SessionLogError) as caught:
        save_session(closed_record, output)
    assert not output.exists() and "TEXTO_RESERVADO" not in str(caught.value)


def test_old_format_still_round_trips_without_new_fields(tmp_path):
    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), Client())
    runtime.ask("Pregunta")
    runtime.close()
    record = load_session(save_session(runtime.session_dict(), tmp_path))
    assert record["session_version"] == "1.0.0" and "context_events" not in record

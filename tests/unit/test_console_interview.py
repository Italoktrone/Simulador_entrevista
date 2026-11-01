"""Contador, interfaz y cierre, con respuestas simuladas y sin red."""

from copy import deepcopy
import json

import pytest

from harness.application.cli import run_console
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse, LLMTimeoutError, LLMInvalidResponseError
from harness.llm.config import OllamaSettings
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import PromptBuildError, load_instructions
from harness.runtime import InterviewFinishedError, InterviewRuntime
from scripts import run_interview


class FakeClient:
    provider = "ollama"

    def __init__(self, answer=None, action=None):
        self.settings = OllamaSettings()
        self.answer = answer
        self.action = action
        self.messages = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def generate(self, messages):
        self.messages.append(deepcopy(messages))
        if self.action is not None:
            self.action()
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer or LLMResponse("Respuesta simulada.", "gemma3n:e2b", "ollama", 1.25)


@pytest.fixture
def setup(tmp_path):
    original = load_interview_setup()
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_bytes(original.candidate.source_path.read_bytes())
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(original.config_dict() | {"max_questions": 2}), encoding="utf-8")
    return load_interview_setup(config_path=config_path, candidate_path=candidate_path)


def runtime_for(setup, client=None):
    return InterviewRuntime(setup, load_instructions(), client if client is not None else FakeClient())


def drive(runtime, entries):
    iterator = iter(entries)
    output = []

    def read(_):
        try:
            item = next(iterator)
        except StopIteration:
            pytest.fail("La consola pidió una entrada adicional inesperada.")
        if isinstance(item, BaseException):
            raise item
        return item

    code = run_console(runtime, provider="ollama", model="gemma3n:e2b", input_fn=read, output_fn=output.append)
    return code, "\n".join(output)


def test_runtime_preserves_question_and_includes_completed_history(setup):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    question = "  ¿Dónde estudiaste?\n"
    assert runtime.ask(question).text == "Respuesta simulada."
    runtime.ask("¿Has utilizado Kubernetes?")
    assert client.messages[0][1] == {"role": "user", "content": question}
    assert client.messages[0][0] == client.messages[1][0]
    assert [item["role"] for item in client.messages[1]] == ["system", "user", "assistant", "user"]
    assert client.messages[1][1:3] == [
        {"role": "user", "content": question},
        {"role": "assistant", "content": "Respuesta simulada."},
    ]
    assert runtime.questions_asked == 2 and runtime.finished
    setup.candidate.assert_source_unchanged()


@pytest.mark.parametrize("question", [None, "", " \t", 7, True])
def test_invalid_question_does_not_consume_a_slot_or_call_model(setup, question):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    with pytest.raises(PromptBuildError):
        runtime.ask(question)
    assert runtime.questions_asked == 0 and client.messages == []


@pytest.mark.parametrize("instructions", [None, " "])
def test_invalid_instructions_fail_before_runtime_starts(setup, instructions):
    with pytest.raises(PromptBuildError):
        InterviewRuntime(setup, instructions, FakeClient())


def test_configured_limit_and_default_twenty_are_enforced(setup):
    for scenario in (setup, load_interview_setup()):
        client = FakeClient()
        runtime = runtime_for(scenario, client)
        limit = scenario.config_dict()["max_questions"]
        for _ in range(limit):
            runtime.ask("Pregunta independiente.")
        with pytest.raises(InterviewFinishedError):
            runtime.ask("Pregunta fuera del límite.")
        assert runtime.questions_asked == len(client.messages) == limit
        assert runtime.finished
    assert limit == 20


def test_provider_failure_counts_once_and_does_not_retry_generation(setup):
    client = FakeClient(answer=LLMTimeoutError("Espera agotada simulada."))
    runtime = runtime_for(setup, client)
    with pytest.raises(LLMTimeoutError):
        runtime.ask("Primera pregunta.")
    assert runtime.questions_asked == 1 and len(client.messages) == 1
    assert not runtime.finished


def test_truncated_answer_is_not_returned_as_a_valid_answer(setup):
    client = FakeClient(answer=LLMResponse("Texto parcial.", "simulado", "ollama", 1.0, finish_reason="length"))
    runtime = runtime_for(setup, client)
    with pytest.raises(LLMInvalidResponseError, match="incompleta"):
        runtime.ask("Pregunta.")
    assert runtime.questions_asked == 1


def test_close_is_idempotent_and_prevents_further_questions(setup):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    runtime.close()
    runtime.close()
    with pytest.raises(InterviewFinishedError):
        runtime.ask("Pregunta.")
    assert client.messages == [] and runtime.finished


def test_execution_counters_are_independent_and_read_only(setup):
    first = runtime_for(setup)
    second = runtime_for(setup)
    first.ask("Pregunta.")
    assert first.questions_asked == 1 and second.questions_asked == 0
    with pytest.raises(AttributeError):
        first.questions_asked = 0


def test_changed_source_prevents_dispatch_and_closes_runtime(setup):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    setup.candidate.source_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("Pregunta.")
    assert runtime.finished and runtime.questions_asked == 0 and client.messages == []


@pytest.mark.parametrize("generation_fails", [False, True])
def test_source_change_during_generation_is_detected_even_after_provider_error(setup, generation_fails):
    client = FakeClient(
        answer=LLMTimeoutError("Fallo simulado.") if generation_fails else None,
        action=lambda: setup.candidate.source_path.write_text("{}", encoding="utf-8"),
    )
    runtime = runtime_for(setup, client)
    with pytest.raises(ProfileIntegrityError):
        runtime.ask("Pregunta.")
    assert runtime.finished and runtime.questions_asked == 1


def test_menu_cv_job_and_empty_inputs_do_not_call_model_or_count_questions(setup):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    code, text = drive(runtime, ["", "Una pregunta antes de iniciar", "/cv", "/puesto", "/ayuda", "/desconocido", "/salir"])
    assert code == 0 and runtime.finished and runtime.questions_asked == 0
    assert client.messages == []
    assert "CURRÍCULUM RESUMIDO" in text and "Instituto Profesional Horizonte Digital" in text
    assert "Aplicaciones Nexo" in text and "Resolución de problemas" in text
    assert "Usa /iniciar" in text and "Comando no reconocido" in text
    private_story = setup.candidate.to_dict()["behavioral_situations"][0]["context"]
    assert private_story not in text


def test_console_accepts_questions_and_restarting_does_not_reset_limit(setup):
    client = FakeClient()
    runtime = runtime_for(setup, client)
    code, text = drive(runtime, [" /INICIAR ", " ", "Primera.", "/iniciar", "/cv", "Segunda."])
    assert code == 0 and runtime.questions_asked == 2
    assert [messages[-1]["content"] for messages in client.messages] == ["Primera.", "Segunda."]
    assert text.count("Candidato: Respuesta simulada.") == 2
    assert "contador se conserva" in text and "Límite de 2" in text


def test_console_recovers_from_technical_error_without_retrying_or_exceeding_limit(setup):
    client = FakeClient(answer=LLMTimeoutError("Espera agotada simulada."))
    runtime = runtime_for(setup, client)
    code, text = drive(runtime, ["/iniciar", "Primera.", "Segunda."])
    assert code == 0 and len(client.messages) == 2 and runtime.questions_asked == 2
    assert "No se obtuvo una respuesta válida" in text and "Límite de 2" in text
    assert text.count("Puedes formular otra") == 1
    assert "Candidato: Respuesta" not in text


def test_console_hides_truncated_text_and_allows_early_exit(setup):
    client = FakeClient(answer=LLMResponse("TEXTO_PARCIAL_NO_PRESENTAR", "simulado", "ollama", 1.0, finish_reason="length"))
    runtime = runtime_for(setup, client)
    code, text = drive(runtime, ["/iniciar", "Pregunta.", "/salir"])
    assert code == 0 and runtime.questions_asked == 1
    assert "TEXTO_PARCIAL_NO_PRESENTAR" not in text and "incompleta" in text


@pytest.mark.parametrize("ending", [EOFError(), KeyboardInterrupt()])
@pytest.mark.parametrize("started", [False, True])
def test_console_closes_on_eof_or_interrupt(setup, ending, started):
    runtime = runtime_for(setup)
    code, _ = drive(runtime, (["/iniciar"] if started else []) + [ending])
    assert code == 0 and runtime.finished and runtime.questions_asked == 0


def test_console_handles_interrupt_while_waiting_for_candidate(setup):
    client = FakeClient(answer=KeyboardInterrupt())
    runtime = runtime_for(setup, client)
    code, text = drive(runtime, ["/iniciar", "Pregunta."])
    assert code == 0 and runtime.finished and runtime.questions_asked == 1
    assert len(client.messages) == 1 and "interrumpida" in text


def test_entry_point_uses_shared_runtime_closes_client_and_checks_integrity(setup, monkeypatch, capsys):
    client = FakeClient()
    monkeypatch.setattr(run_interview, "load_interview_setup", lambda: setup)
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr(run_interview, "run_console", lambda runtime, **_: drive(runtime, ["/iniciar", "Pregunta.", "/salir"])[0])
    assert run_interview.main() == 0
    assert client.closed and len(client.messages) == 1
    assert "Archivo original del candidato intacto" in capsys.readouterr().out


@pytest.mark.parametrize("component", ["load_interview_setup", "load_instructions", "create_client"])
def test_entry_point_reports_preparation_error_without_traceback(setup, monkeypatch, capsys, component):
    monkeypatch.setattr(run_interview, "load_interview_setup", lambda: setup)

    def fail():
        raise ValueError("Configuración inválida simulada.")

    monkeypatch.setattr(run_interview, component, fail)
    assert run_interview.main() == 1
    text = capsys.readouterr().out
    assert "Configuración inválida simulada" in text and "Traceback" not in text


def test_entry_point_reports_integrity_failure_without_claiming_original_intact(setup, monkeypatch, capsys):
    client = FakeClient(action=lambda: setup.candidate.source_path.write_text("{}", encoding="utf-8"))
    monkeypatch.setattr(run_interview, "load_interview_setup", lambda: setup)
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    monkeypatch.setattr(run_interview, "run_console", lambda runtime, **_: drive(runtime, ["/iniciar", "Pregunta."])[0])
    assert run_interview.main() == 1
    text = capsys.readouterr().out
    assert "Error de integridad" in text and "Archivo original del candidato intacto" not in text
    assert client.closed

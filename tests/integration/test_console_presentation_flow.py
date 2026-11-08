"""Lectura y consulta de respuestas sin nuevas inferencias ni cambios del registro."""

from copy import deepcopy

import pytest

from harness.application.cli import run_console, format_job, format_resume
from harness.application.console_view import format_evaluation, format_saved_response, WIDTH
from harness.llm.client import LLMResponse, LLMTimeoutError
from tests.integration.test_question_evaluation_flow import make_runtime
from tests.integration.test_pre_response_classification import CandidateClient


def drive(runtime, entries):
    outputs = []
    inputs = iter(entries)
    run_console(runtime, provider="ollama", model="simulado",
                input_fn=lambda _: next(inputs), output_fn=outputs.append)
    return "\n".join(outputs)


def test_lookup_preserves_session_and_matches_evaluation_by_question_number():
    runtime = make_runtime()
    runtime.ask("Hola")  # Intervención sin pregunta enviada; no debe desplazar la evaluación.
    runtime.ask("¿Has utilizado Git?")
    runtime.ask("¿Has utilizado Python?")
    original = runtime.session_dict()
    history = runtime.history_messages()
    text = format_saved_response(original, 2)
    assert "CONSULTA | PREGUNTA 02" in text
    assert "¿Has utilizado Python?" in text and "¿Has utilizado Git?" not in text
    assert "RESPUESTA DEL CANDIDATO | PREGUNTA 02/20" in text
    assert "EVALUACIÓN DE LA PREGUNTA 02" in text
    assert runtime.session_dict() == original and runtime.history_messages() == history


def test_read_commands_do_not_dispatch_or_consume_questions():
    candidate = CandidateClient()
    runtime = make_runtime(candidate=candidate)
    text = drive(runtime, ["/respuestas", "/menu", "/iniciar", "¿Has utilizado Git?",
                           "/respuestas", "/respuesta 1", "/respuesta 20", "/sesion", "/salir"])
    assert "Todavía no se han enviado preguntas" in text
    assert "Pregunta 01 | Respuesta completa" in text
    assert "No existe esa pregunta" in text
    assert text.count("RESPUESTA DEL CANDIDATO | PREGUNTA 01/20") == 2
    assert len(candidate.requests) == runtime.questions_asked == 1
    assert len(runtime.session_dict()["interventions"]) == 1


@pytest.mark.parametrize("command", ["/respuesta", "/respuesta 0", "/respuesta -1",
    "/respuesta abc", "/respuesta 1 2", "/respuesta ١", "/respuesta " + "9" * 5000])
def test_invalid_lookup_explains_usage_without_dispatch(command):
    candidate = CandidateClient()
    runtime = make_runtime(candidate=candidate)
    text = drive(runtime, [command, "/salir"])
    assert "Usa /respuesta N" in text
    assert not candidate.requests and runtime.questions_asked == 0


@pytest.mark.parametrize("failure", [LLMTimeoutError("Fallo simulado."),
    LLMResponse("CONTENIDO_INCOMPLETO_NO_MOSTRAR", "simulado", "ollama", 0.1, finish_reason="length")])
def test_failed_answer_remains_numbered_and_never_exposes_incomplete_text(failure):
    runtime = make_runtime(candidate=CandidateClient(outcomes=[failure]))
    text = drive(runtime, ["/iniciar", "¿Has utilizado Git?", "/respuestas", "/respuesta 1", "/salir"])
    assert "Pregunta 01 |" in text and "ESTADO DE LA RESPUESTA" in text
    assert "No hay una respuesta completa disponible" in text
    assert "CONTENIDO_INCOMPLETO_NO_MOSTRAR" not in text
    assert "RESPUESTA DEL CANDIDATO |" not in text


def test_wrapping_preserves_long_answer_content_and_paragraph_boundaries():
    answer = " ".join(f"palabra{i}" for i in range(80)) + "\n\nSegundo párrafo independiente."
    runtime = make_runtime(candidate=CandidateClient(outcomes=[LLMResponse(answer, "simulado", "ollama", 0.5)]))
    runtime.ask("¿Has utilizado Git?")
    session = runtime.session_dict()
    text = format_saved_response(session, 1)
    assert all(len(line) <= WIDTH for line in text.splitlines())
    assert all(word in text for word in answer.split())
    assert "\n\n  Segundo párrafo independiente." in text
    assert session["attempts"][0]["response"]["text"] == answer


def test_partial_evaluation_does_not_invent_a_global_level_or_missing_criterion():
    runtime = make_runtime()
    runtime.ask("¿Has utilizado Git?")
    record = deepcopy(runtime.last_evaluation)
    record.update(status="parcial", visible_level=None, normalized_score=None, weighted_score=None,
                  explanation="Evaluación parcial, sin nivel global.")
    record["analysis"]["criteria"]["claridad"]["level"] = None
    text = format_evaluation(record)
    assert "Resultado: Evaluación parcial, sin nivel global" in text
    assert "Claridad: Sin evidencia suficiente" in text
    assert "Resultado: Logrado" not in text and "None" not in text


def test_public_documents_have_readable_width_without_mutating_their_data():
    runtime = make_runtime()
    job = runtime.setup.job_dict()
    original = deepcopy(job)
    for text in (format_resume(runtime.setup.candidate), format_job(job)):
        assert all(len(line) <= WIDTH for line in text.splitlines())
    assert job == original

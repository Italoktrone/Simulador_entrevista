"""Cargar archivos de sesión reales y emitir el diagnóstico sin red ni escritura."""

import httpx
import pytest

from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import save_session
from scripts import inspect_context


class Client:
    def generate(self, messages):
        return LLMResponse(text="RESPUESTA_RESERVADA", model="modelo-simulado", provider="ollama",
                           elapsed_seconds=0.1, input_tokens=6097, cached_input_tokens=6075, finish_reason="stop")


@pytest.mark.parametrize("has_question", [True, False])
def test_inspection_is_read_only_and_never_calls_http(tmp_path, monkeypatch, capsys, has_question):
    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), Client(), provider="ollama", model="modelo-simulado")
    if has_question:
        runtime.ask("PREGUNTA_RESERVADA")
    runtime.close("user_exit")
    path = save_session(runtime.session_dict(), tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def no_network(*args, **kwargs):
        pytest.fail("El diagnóstico no debe consultar al proveedor")

    monkeypatch.setattr(httpx.Client, "send", no_network)
    assert inspect_context.main([str(path), "--context-size", "8192", "--max-output-tokens", "512", "--safety-margin", "256"]) == 0
    text = capsys.readouterr().out
    assert runtime.session_id in text and "7424" in text
    assert "RESPUESTA_RESERVADA" not in text and "PREGUNTA_RESERVADA" not in text
    assert ("entrada informada=6097" in text and "límite=1327" in text) if has_question else "Sin intentos registrados" in text
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("args", [[], ["--context-size", "100", "--max-output-tokens", "512"]])
def test_invalid_path_or_budget_reports_error_without_creating_files(tmp_path, capsys, args):
    assert inspect_context.main([str(tmp_path / "missing.json"), *args]) == 1
    text = capsys.readouterr().out
    assert "No se pudo revisar el contexto:" in text and "DIAGNÓSTICO DEL CONTEXTO REGISTRADO" not in text
    assert list(tmp_path.iterdir()) == []

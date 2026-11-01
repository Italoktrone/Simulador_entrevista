"""Vista previa por el adaptador real, sin modificar el archivo de origen."""

import json

import httpx
import pytest

from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse, LLMTimeoutError
from harness.llm.factory import create_client
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import save_session
from scripts import preview_summary


def archive(tmp_path):
    outcomes = iter([
        LLMResponse("Inventario Aula fue académico. Usé Python. Esta frase introduce la respuesta. No tuvo clientes comerciales.", "simulado", "ollama", 0.1),
        LLMTimeoutError("Reservado"),
        LLMResponse("Era Inventario Aula.", "simulado", "ollama", 0.1),
    ])

    class Client:
        def generate(self, messages):
            value = next(outcomes)
            if isinstance(value, BaseException):
                raise value
            return value

    runtime = InterviewRuntime(load_interview_setup(), load_instructions(), Client())
    runtime.ask("Proyecto académico")
    with pytest.raises(LLMTimeoutError):
        runtime.ask("TEXTO_FALLIDO_NO_ENVIAR")
    runtime.ask("¿Cómo se llamaba?")
    runtime.close("user_exit")
    return save_session(runtime.session_dict(), tmp_path)


def test_preview_selects_literal_sources_and_keeps_file_bytes(monkeypatch, capsys, tmp_path):
    path = archive(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["truncate"] is False and payload["shift"] is False
        assert payload["model"] == "gemma4:e4b" and payload["think"] is False
        assert [m["role"] for m in payload["messages"]] == ["system", "user"]
        source = json.loads(payload["messages"][1]["content"])
        assert len(source["old_turns"]) == 1
        assert "TEXTO_FALLIDO_NO_ENVIAR" not in str(source) and "candidate_profile" not in str(source)
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": '{"selections":[{"question_number":1,"segment_indices":[1,4]}]}'}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(preview_summary, "create_client", lambda: client)
    assert preview_summary.main([str(path), "--keep-recent-pairs", "1"]) == 0
    output = capsys.readouterr().out
    assert "[P1/F4] No tuvo clientes comerciales." in output and "Fragmentos omitidos: [3]" in output
    assert "Fragmentos conservados por protección: [2]" in output
    assert "Pregunta reciente 3 (completa)" in output and "Era Inventario Aula." in output
    assert "PENDIENTE DE REVISIÓN" in output and "Procedencia y citas verificadas" in output
    assert len(requests) == 1 and client._http.is_closed
    assert {p: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_preview_without_older_turns_never_creates_client(monkeypatch, capsys, tmp_path):
    path = archive(tmp_path)
    monkeypatch.setattr(preview_summary, "create_client", lambda: pytest.fail("No se necesita proveedor"))
    assert preview_summary.main([str(path)]) == 0
    assert "no se consultó un modelo" in capsys.readouterr().out


@pytest.mark.parametrize("error", ["free_text", "interrupted"])
def test_failed_preview_does_not_print_a_valid_proposal_or_modify_files(monkeypatch, capsys, tmp_path, error):
    path = archive(tmp_path)
    before = path.read_bytes()

    def handler(request):
        if error == "interrupted":
            raise KeyboardInterrupt()
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": "PROPUESTA_INVENTADA"}})

    client = create_client({"OLLAMA_MODEL": "gemma4:e4b"}, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(preview_summary, "create_client", lambda: client)
    assert preview_summary.main([str(path), "--keep-recent-pairs", "1"]) == 1
    output = capsys.readouterr().out
    assert "PENDIENTE DE REVISIÓN" not in output and "PROPUESTA_INVENTADA" not in output
    assert path.read_bytes() == before and client._http.is_closed

"""La prueba aislada conserva evidencia tanto de éxito como de fallo técnico."""

import json

import httpx
import pytest

from harness.interview_config import load_interview_setup
from harness.llm.client import LLMConnectionError, LLMResponse
from harness.llm.config import OllamaSettings
from harness.llm.factory import create_client
from scripts import smoke_test


@pytest.mark.parametrize("connection_fails, finish_reason, status, exit_code", [
    (False, "stop", "completed", 0),
    (True, "stop", "error", 1),
    (False, "length", "incomplete", 1),
])
def test_smoke_evidence_and_exit_status(tmp_path, monkeypatch, capsys, connection_fails, finish_reason, status, exit_code):
    setup = load_interview_setup()
    monkeypatch.setattr(smoke_test, "ROOT", tmp_path)
    monkeypatch.setattr(smoke_test, "load_interview_setup", lambda: setup)

    class FakeClient:
        provider = "ollama"

        def __init__(self, settings):
            assert settings.model == "gemma3n:e2b"
            self.settings = settings

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def generate(self, messages):
            assert messages[-1]["content"] == smoke_test.QUESTION
            if connection_fails:
                raise LLMConnectionError("Servicio no disponible.")
            return LLMResponse("Respuesta simulada.", "gemma3n:e2b", "ollama", 1.25, 4311, 20, finish_reason)

    monkeypatch.setattr(smoke_test, "create_client", lambda: FakeClient(OllamaSettings()))
    assert smoke_test.main() == exit_code
    files = list((tmp_path / "outputs" / "results").glob("ollama-smoke-*.json"))
    assert len(files) == 1
    evidence = json.loads(files[0].read_text(encoding="utf-8"))
    assert evidence["status"] == status
    assert evidence["profile_unchanged"] is True
    assert evidence["candidate_source_sha256"] == setup.candidate.source_sha256
    assert evidence["semantic_review"] == "pendiente de revisión humana"
    assert evidence["test_elapsed_seconds"] >= 0
    if connection_fails:
        assert evidence["error_type"] == "LLMConnectionError"
        assert "response" not in evidence
    else:
        assert evidence["response"]["text"] == "Respuesta simulada."
        assert "messages" not in evidence
    if finish_reason == "length":
        assert "Respuesta simulada." not in capsys.readouterr().out
    setup.candidate.assert_source_unchanged()


def test_smoke_records_blocked_external_selection_without_sending_or_logging_key(tmp_path, monkeypatch, capsys):
    key = "clave-ficticia-solo-pruebas"
    values = {
        "LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "false",
        "OPENAI_MODEL": "modelo-ficticio-001", "OPENAI_API_KEY": key,
    }

    def handler(_):
        pytest.fail("La API desactivada no debe recibir solicitudes.")

    monkeypatch.setattr(smoke_test, "ROOT", tmp_path)
    monkeypatch.setattr(smoke_test, "create_client", lambda: create_client(values, transport=httpx.MockTransport(handler)))
    assert smoke_test.main() == 1
    files = list((tmp_path / "outputs" / "results").glob("llm-smoke-*.json"))
    assert len(files) == 1
    raw = files[0].read_text(encoding="utf-8")
    evidence = json.loads(raw)
    assert evidence["error_type"] == "LLMConfigurationError"
    assert evidence["profile_unchanged"] is None
    assert key not in raw + capsys.readouterr().out


def test_smoke_can_use_external_adapter_with_mock_transport_and_safe_evidence(tmp_path, monkeypatch, capsys):
    key = "clave-ficticia-solo-pruebas"
    values = {
        "LLM_PROVIDER": "openai", "LLM_ALLOW_EXTERNAL_API": "true",
        "OPENAI_MODEL": "modelo-ficticio-001", "OPENAI_API_KEY": key,
    }

    def handler(request):
        assert request.url.host == "api.openai.com"
        return httpx.Response(200, json={
            "model": values["OPENAI_MODEL"], "status": "completed",
            "output": [{"type": "message", "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": "Respuesta simulada."}]}],
        })

    monkeypatch.setattr(smoke_test, "ROOT", tmp_path)
    monkeypatch.setattr(smoke_test, "create_client", lambda: create_client(values, transport=httpx.MockTransport(handler)))
    assert smoke_test.main() == 0
    files = list((tmp_path / "outputs" / "results").glob("openai-smoke-*.json"))
    assert len(files) == 1
    raw = files[0].read_text(encoding="utf-8")
    evidence = json.loads(raw)
    assert evidence["provider"] == "openai"
    assert evidence["settings"]["model"] == values["OPENAI_MODEL"]
    assert evidence["response"]["finish_reason"] == "completed"
    assert evidence["profile_unchanged"] is True
    assert "Modelo externo" in capsys.readouterr().out
    assert key not in raw

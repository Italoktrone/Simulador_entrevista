"""UNAB y selector: HTTP simulado, configuración privada y ausencia de secretos."""

from dataclasses import asdict
import json
from types import SimpleNamespace

import httpx
import pytest

from harness.llm.client import LLMAuthenticationError, LLMInvalidResponseError, LLMProviderError, LLMTimeoutError
from harness.llm.config import LLMConfigurationError
from harness.llm.factory import create_client
from harness.llm.unab_client import UNABSettings
from harness.session_log import load_session
from harness import session_log
from scripts import run_interview, start_interview


KEY = "clave-ficticia-solo-test"
CONFIG = {"local_model": "gemma4:e4b", "api_model": "gemma4:26b", "api_key": KEY}
ENV = {"LLM_PROVIDER": "unab", "LLM_ALLOW_EXTERNAL_API": "true", "UNAB_API_KEY": KEY}


def reply(reason="stop", content="Estudié Ingeniería en Informática."):
    return {"model": "gemma4:26b", "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": reason}],
            "usage": {"prompt_tokens": 123, "completion_tokens": 8}}


def test_unab_request_uses_only_expected_host_path_and_header_and_preserves_messages():
    messages = [{"role": "system", "content": "Reglas"}, {"role": "user", "content": "Pregunta"}]
    def handler(request):
        assert str(request.url) == "https://quotas.devhub.cl/api/v1/chat/completions"
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        assert json.loads(request.content) == {"model": "gemma4:26b", "messages": messages, "max_tokens": 2048, "stream": False, "reasoning_effort": "none"}
        return httpx.Response(200, json=reply())
    with create_client(ENV, transport=httpx.MockTransport(handler)) as client:
        response = client.generate(messages)
        assert response.provider == "unab" and response.input_tokens == 123
        assert response.finish_reason == "stop" and response.text == reply()["choices"][0]["message"]["content"]
        assert KEY not in repr(client.settings) + json.dumps(asdict(response))
    assert client._http.is_closed


@pytest.mark.parametrize("reason", ["length", "stop"])
def test_finish_reason_is_preserved(reason):
    with create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=reply(reason)))) as client:
        assert client.generate([{"role": "user", "content": "Pregunta"}]).finish_reason == reason


@pytest.mark.parametrize("data", [{}, [], {"choices": []}, reply(content=""), reply(content="<think>privado</think>"), reply(reason={}), reply(reason="tool_calls")])
def test_invalid_responses_fail_safely(data):
    with create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data))) as client:
        with pytest.raises(LLMInvalidResponseError):
            client.generate([{"role": "user", "content": "Pregunta"}])


@pytest.mark.parametrize("status,cls", [(401, LLMAuthenticationError), (403, LLMAuthenticationError), (429, LLMProviderError), (500, LLMProviderError)])
def test_http_errors_do_not_echo_bodies_or_credentials(status, cls):
    with create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(status, text=KEY))) as client:
        with pytest.raises(cls) as caught:
            client.generate([{"role": "user", "content": "Pregunta"}])
        assert KEY not in str(caught.value)


def test_generation_timeout_is_not_retried():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout(KEY)
    with create_client(ENV, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMTimeoutError):
            client.generate([{"role": "user", "content": "Pregunta"}])
    assert len(calls) == 1


def test_api_is_explicit_and_destination_cannot_be_changed():
    with pytest.raises(LLMConfigurationError):
        create_client(ENV | {"LLM_ALLOW_EXTERNAL_API": "false"})
    with pytest.raises(LLMConfigurationError):
        create_client(ENV | {"UNAB_API_KEY": ""})
    with pytest.raises(LLMConfigurationError):
        UNABSettings(base_url="https://otro.example/api/v1/")


def test_selector_local_disables_external_even_with_old_api_environment():
    env = start_interview.selected_environment(CONFIG, "1", ENV)
    assert env["LLM_PROVIDER"] == "ollama" and env["LLM_ALLOW_EXTERNAL_API"] == "false"
    assert "UNAB_API_KEY" not in env and CONFIG["api_key"] == KEY
    with pytest.raises(ValueError):
        start_interview.selected_environment(CONFIG | {"api_key": ""}, "2", {})


@pytest.mark.parametrize("selection", ["1", "2"])
def test_launcher_passes_key_only_in_child_environment_not_command(monkeypatch, tmp_path, selection):
    path = tmp_path / "private.json"
    path.write_text(json.dumps(CONFIG), encoding="utf-8")
    monkeypatch.setattr(start_interview, "CONFIG_PATH", path)
    monkeypatch.setattr("builtins.input", lambda _: selection)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert KEY not in " ".join(command)
        assert kwargs["env"]["LLM_PROVIDER"] == ("ollama" if selection == "1" else "unab")
        if selection == "2":
            assert kwargs["env"]["UNAB_API_KEY"] == KEY
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(start_interview.subprocess, "run", run)
    assert start_interview.main() == 0 and len(calls) == 1


def test_bad_private_config_does_not_print_its_contents(monkeypatch, tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text('{"api_key":"' + KEY, encoding="utf-8")
    monkeypatch.setattr(start_interview, "CONFIG_PATH", path)
    assert start_interview.main() == 1
    assert KEY not in capsys.readouterr().out


def test_unab_console_saves_session_without_key(monkeypatch, capsys):
    client = create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=reply())))
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    entries = iter(["/iniciar", "¿Dónde estudiaste?", "/salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main() == 0
    session = load_session(next(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json")))
    assert session["requested_provider"] == "unab" and session["attempts"][0]["status"] == "completed"
    assert "UNAB IA (externo)" in capsys.readouterr().out
    assert KEY not in json.dumps(session, ensure_ascii=False)


@pytest.mark.parametrize("content", [None, "", "  "])
def test_reasoning_only_at_limit_preserves_usage_but_never_reasoning_or_prompts(content):
    data = reply(reason="length", content=content)
    data["choices"][0]["message"]["reasoning"] = "RAZONAMIENTO_RESERVADO"
    data["usage"] = {"prompt_tokens": 6060, "completion_tokens": 512, "total_tokens": 6572,
                     "completion_tokens_details": {"reasoning_tokens": 512}}
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=data)
    with create_client(ENV | {"UNAB_MAX_OUTPUT_TOKENS": "512"}, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(LLMInvalidResponseError, match="límite de salida"):
            client.generate([{"role": "user", "content": "PREGUNTA_RESERVADA"}])
        diagnostics = client.call_diagnostics
        assert diagnostics[0]["validation_status"] == "length_without_final_text"
        assert diagnostics[0]["prompt_tokens"] == 6060 and diagnostics[0]["completion_tokens"] == 512
        assert diagnostics[0]["reasoning_tokens"] == 512 and diagnostics[0]["reasoning_present"] is True
        assert len(calls) == 1
        assert not any(s in json.dumps(diagnostics) for s in (KEY, "RAZONAMIENTO_RESERVADO", "PREGUNTA_RESERVADA"))
        diagnostics[0]["prompt_tokens"] = 0
        assert client.call_diagnostics[0]["prompt_tokens"] == 6060


@pytest.mark.parametrize("text", ["<|channel>thought oculto<channel|>respuesta", "<think>oculto</think>respuesta"])
def test_mixed_reasoning_is_not_shown_and_usage_is_retained(text):
    with create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=reply(content=text)))) as client:
        with pytest.raises(LLMInvalidResponseError):
            client.generate([{"role": "user", "content": "Pregunta"}])
        assert client.call_diagnostics[0]["completion_tokens"] == 8
        assert text not in json.dumps(client.call_diagnostics)


def test_console_records_error_usage_separately_and_missing_usage_stays_unknown(monkeypatch, capsys):
    data = reply(reason="length", content=None)
    data["choices"][0]["message"]["reasoning_content"] = "RAZONAMIENTO_RESERVADO"
    del data["usage"]
    client = create_client(ENV, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=data)))
    monkeypatch.setattr(run_interview, "create_client", lambda: client)
    entries = iter(["/iniciar", "Pregunta", "/salir"])
    monkeypatch.setattr("builtins.input", lambda _: next(entries))
    assert run_interview.main() == 0
    session = load_session(next(session_log.DEFAULT_SESSIONS_DIR.glob("session-*.json")))
    diagnostics_path = session_log.DEFAULT_SESSIONS_DIR.parent / "results" / f"unab-usage-{session['session_id']}.json"
    diagnostic_text = diagnostics_path.read_text(encoding="utf-8")
    diagnostics = json.loads(diagnostic_text)["calls"]
    assert diagnostics[0]["prompt_tokens"] is None and diagnostics[0]["completion_tokens"] is None
    assert session["attempts"][0]["status"] == "error"
    output = capsys.readouterr().out
    assert "Diagnóstico de uso de API guardado:" in output
    assert not any(s in output + diagnostic_text + json.dumps(session) for s in (KEY, "RAZONAMIENTO_RESERVADO"))


@pytest.mark.parametrize("budget", [16, 512, 2048, 4096])
def test_explicit_unab_budget_reaches_request_and_diagnostics(budget):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json=reply())
    with create_client(ENV | {"UNAB_MAX_OUTPUT_TOKENS": str(budget)}, transport=httpx.MockTransport(handler)) as client:
        client.generate([{"role": "user", "content": "Pregunta"}])
        assert calls[0]["max_tokens"] == budget
        assert client.call_diagnostics[0]["requested_max_tokens"] == budget


@pytest.mark.parametrize("budget", [0, 15, 4097, True, "2048", None, 2048.5])
def test_invalid_private_budget_rejected_before_external_run(budget):
    with pytest.raises(ValueError, match="api_max_output_tokens"):
        start_interview.selected_environment(CONFIG | {"api_max_output_tokens": budget}, "2", {})
    # La selección local no depende del presupuesto de un proveedor externo.
    assert start_interview.selected_environment(CONFIG | {"api_max_output_tokens": budget}, "1", {})["LLM_PROVIDER"] == "ollama"


@pytest.mark.parametrize("budget", ["", "abc", "15", "4097", "512.5"])
def test_invalid_environment_budget_rejected(budget):
    with pytest.raises(LLMConfigurationError, match="UNAB_MAX_OUTPUT_TOKENS"):
        create_client(ENV | {"UNAB_MAX_OUTPUT_TOKENS": budget})


def test_budget_default_does_not_override_private_choice_or_change_other_providers():
    env = start_interview.selected_environment(CONFIG, "2", {"UNAB_MAX_OUTPUT_TOKENS": "4096"})
    assert env["UNAB_MAX_OUTPUT_TOKENS"] == "2048"
    env = start_interview.selected_environment(CONFIG | {"api_max_output_tokens": 1024}, "2", {})
    assert env["UNAB_MAX_OUTPUT_TOKENS"] == "1024"
    assert UNABSettings().max_output_tokens == 2048
    with pytest.raises(LLMConfigurationError):
        UNABSettings(max_output_tokens=4097)
    with create_client({}) as client:
        assert client.settings.max_output_tokens == 512

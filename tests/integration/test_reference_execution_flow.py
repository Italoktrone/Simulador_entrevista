"""Lote real con HTTP simulado: aislamiento, persistencia y fallos seguros."""

import json

import httpx
import pytest

from harness.llm.factory import create_client
from harness.session_log import SessionLogError, load_session
from scripts import run_reference_cases


@pytest.fixture
def batch(monkeypatch, tmp_path):
    output = tmp_path / "results"
    monkeypatch.setattr(run_reference_cases, "RESULTS_DIR", output)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_ALLOW_EXTERNAL_API", "true")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4:e4b")
    return output


def install_client(monkeypatch, handler):
    clients = []

    def factory(values):
        assert values["LLM_PROVIDER"] == "ollama" and values["LLM_ALLOW_EXTERNAL_API"] == "false"
        client = create_client(values, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    monkeypatch.setattr(run_reference_cases, "create_client", factory)
    return clients


def read_report(output):
    paths = list(output.glob("reference-run-*.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text(encoding="utf-8"))


def test_four_cases_isolated_and_continuity_preserved_without_automatic_judgment(batch, monkeypatch):
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
                                        "message": {"role": "assistant", "content": f"Respuesta simulada {len(requests)}"}})

    clients = install_client(monkeypatch, handler)
    assert run_reference_cases.main([]) == 0
    report = read_report(batch)
    assert report["technical_status"] == "completed" and report["semantic_review"] == "pending_human_review"
    assert report["not_executed_case_ids"] == [] and report["sources_unchanged"]
    assert len(set(c["session_id"] for c in report["cases"])) == 4
    assert [len(p["messages"]) for p in requests] == [2, 2, 2, 4, 2]
    assert requests[3]["messages"][2] == {"role": "assistant", "content": "Respuesta simulada 3"}
    for case in report["cases"]:
        session = load_session(case["session_file"])
        assert session == case["session_snapshot"]
        assert session["status"] == "closed" and session["source_integrity"] == "unchanged"
        assert set(case["attempt_statuses"]) == {"completed"}
    assert clients[0]._http.is_closed
    assert all(p["model"] == "gemma4:e4b" for p in requests)


@pytest.mark.parametrize("kind,status", [("http", "error"), ("length", "incomplete"), ("interrupt", "interrupted")])
def test_first_failure_stops_batch_and_preserves_session(batch, monkeypatch, capsys, kind, status):
    calls = []

    def handler(request):
        calls.append(request)
        if kind == "interrupt":
            raise KeyboardInterrupt()
        if kind == "http":
            return httpx.Response(500, json={"error": "CONTENIDO_RESERVADO"})
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "length",
                                        "message": {"role": "assistant", "content": "Respuesta parcial"}})

    clients = install_client(monkeypatch, handler)
    assert run_reference_cases.main([]) == 1
    report = read_report(batch)
    assert len(calls) == 1 and len(report["cases"]) == 1 and len(report["not_executed_case_ids"]) == 3
    assert report["cases"][0]["attempt_statuses"] == [status]
    assert load_session(report["cases"][0]["session_file"]) == report["cases"][0]["session_snapshot"]
    assert report["technical_status"] != "completed"
    assert "CONTENIDO_RESERVADO" not in json.dumps(report) + capsys.readouterr().out
    assert clients[0]._http.is_closed


def test_failed_session_save_keeps_snapshot_and_stops(batch, monkeypatch):
    clients = install_client(monkeypatch, lambda request: httpx.Response(200, json={
        "model": "gemma4:e4b", "done": True, "done_reason": "stop",
        "message": {"role": "assistant", "content": "Respuesta simulada"},
    }))

    def fail_save(snapshot):
        raise SessionLogError("fallo simulado")

    monkeypatch.setattr(run_reference_cases, "save_session", fail_save)
    assert run_reference_cases.main(["--model", "qwen3:4b"]) == 1
    report = read_report(batch)
    assert report["settings"]["model"] == "qwen3:4b"
    assert report["technical_status"] == "error" and len(report["cases"]) == 1
    assert report["cases"][0]["session_file"] is None
    assert report["cases"][0]["session_snapshot"]["attempts"][0]["status"] == "completed"
    assert clients[0]._http.is_closed


def test_invalid_suite_prevents_client_creation(batch, monkeypatch):
    def no_client(values):
        pytest.fail("El conjunto inválido debe rechazarse antes de crear un cliente")

    monkeypatch.setattr(run_reference_cases, "create_client", no_client)
    assert run_reference_cases.main(["--suite", str(batch / "missing.json")]) == 1
    report = read_report(batch)
    assert report["technical_status"] == "error" and report["cases"] == []
    assert report["semantic_review"] == "pending_human_review"

"""Logging explícito de tres casos; red simulada y sin cambios en la salida."""

import json

import httpx
import pytest

from harness.classification_references import load_classification_references
from scripts.diagnose_classifier import CASE_IDS, RecordingTransport, diagnose_text


@pytest.fixture(scope="module")
def inputs():
    suite = load_classification_references()
    return {i: suite.input_for(i) for i in CASE_IDS}


def payload(source):
    return {"messages": [{"role": "user", "content": json.dumps({"input": source})}]}


def test_raw_log_preserves_model_content_and_never_logs_thinking_headers_or_request(tmp_path, inputs):
    raw = '  ```json\n{"bad": true}\n```  '
    body = {"message": {"content": raw, "thinking": "NO_GUARDAR_PENSAMIENTO"}}
    delegate = httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    transport = RecordingTransport(tmp_path, inputs, delegate)
    with httpx.Client(transport=transport) as client:
        response = client.post("http://127.0.0.1:11434/api/chat", json=payload(inputs["R04"]))
    assert response.json() == body
    assert (tmp_path / "R04-attempt-1.txt").read_bytes() == raw.encode("utf-8")
    meta = json.loads((tmp_path / "R04-attempt-1.json").read_text(encoding="utf-8"))
    assert meta["diagnosis"]["status"] == "json_invalido"
    assert meta["diagnosis"]["line"] == 1
    assert all("NO_GUARDAR_PENSAMIENTO" not in p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
    assert "messages" not in meta and "headers" not in meta


def test_contract_diagnosis_retains_controlled_rule_and_path(inputs):
    diagnosis = diagnose_text('{}', inputs["R04"])
    assert diagnosis["status"] == "contrato_invalido"
    assert diagnosis["rule"] == "required"


@pytest.mark.parametrize("violation", ["external", "auth", "case", "input"])
def test_recording_rejects_unauthorized_requests_before_contact(tmp_path, inputs, violation):
    transport = RecordingTransport(tmp_path, inputs, httpx.MockTransport(lambda _: pytest.fail("No debe enviar")))
    source = dict(inputs["R04"])
    url, headers = "http://127.0.0.1:11434/api/chat", {}
    if violation == "external":
        url = "https://example.com/api/chat"
    elif violation == "auth":
        headers = {"authorization": "Bearer CLAVE_FICTICIA"}
    elif violation == "case":
        source["intervention_id"] = "R09"
    else:
        source["text"] = "Otra intervención."
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError):
            client.post(url, headers=headers, json=payload(source))
    assert list(tmp_path.iterdir()) == []


def test_recording_never_sends_a_third_attempt(tmp_path, inputs):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"content": "{}"}})
    transport = RecordingTransport(tmp_path, inputs, httpx.MockTransport(handler))
    with httpx.Client(transport=transport) as client:
        for _ in range(2):
            client.post("http://127.0.0.1:11434/api/chat", json=payload(inputs["R04"]))
        with pytest.raises(ValueError, match="tercera"):
            client.post("http://127.0.0.1:11434/api/chat", json=payload(inputs["R04"]))
    assert len(calls) == 2

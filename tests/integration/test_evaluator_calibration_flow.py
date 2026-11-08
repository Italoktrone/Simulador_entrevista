"""A/B local con proveedor simulado: seis llamadas máximas salvo reparación única."""

import json
from types import SimpleNamespace

from harness.llm.client import LLMTimeoutError
from scripts import calibrate_evaluator_few_shot as script
from tests.evaluation_fixtures import EvaluationClient


class LocalClient(EvaluationClient):
    settings = SimpleNamespace(temperature=0, context_size=8192)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_preview_does_not_create_a_client(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("La vista previa no crea clientes.")
    monkeypatch.setattr(script, "create_evaluation_client", forbidden)
    assert script.main(["--model", "gemma4:e4b", "--preview"]) == 0
    output = capsys.readouterr().out
    assert '"model_calls": 0' in output and '"planned_comparisons": 6' in output


def test_ab_uses_same_inputs_and_expected_labels_never_enter_case_payload(monkeypatch, tmp_path):
    client = LocalClient()
    def factory(env, **kwargs):
        assert env == {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": "gemma4:e4b"}
        return client
    monkeypatch.setattr(script, "create_evaluation_client", factory)
    monkeypatch.setattr(script, "source_hashes", lambda: {"fuente": "estable"})
    monkeypatch.setattr(script, "ROOT", tmp_path)
    assert script.main(["--model", "gemma4:e4b"]) == 0
    assert len(client.requests) == 6
    for index in (0, 2, 4):
        assert client.requests[index][1] == client.requests[index + 1][1]
        payload = json.loads(client.requests[index][1]["content"])
        assert set(payload) == {"input"} and "expected" not in payload["input"]
        assert "DEMOSTRACIONES APROBADAS" not in client.requests[index][0]["content"]
        assert "DEMOSTRACIONES APROBADAS" in client.requests[index + 1][0]["content"]
    report = json.loads(next((tmp_path / "outputs/results").glob("*.json")).read_text(encoding="utf-8"))
    assert report["state"] == "completed" and not report["not_executed"]
    assert all(not c["target_in_demonstration_set"] for c in report["cases"] if c["case_id"] == "E11")
    assert all(c["record"]["few_shot"]["case_ids"] == ["E03", "E05", "E07", "E08", "E12", "E15"] for c in report["cases"] if c["mode"] == "few_shot")


def test_transport_failure_stops_without_running_remaining_pairs(monkeypatch, tmp_path):
    client = LocalClient([LLMTimeoutError("PRIVADO")])
    monkeypatch.setattr(script, "create_evaluation_client", lambda *args, **kwargs: client)
    monkeypatch.setattr(script, "source_hashes", lambda: {"fuente": "estable"})
    monkeypatch.setattr(script, "ROOT", tmp_path)
    assert script.main(["--model", "gemma4:e4b"]) == 1
    assert len(client.requests) == 1
    report = json.loads(next((tmp_path / "outputs/results").glob("*.json")).read_text(encoding="utf-8"))
    assert report["state"] == "stopped_on_technical_error" and len(report["not_executed"]) == 5
    assert "PRIVADO" not in json.dumps(report)

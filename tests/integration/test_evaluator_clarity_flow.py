"""Muestra independiente de las demostraciones y continuación sin repetir casos."""

import json
from types import SimpleNamespace

import pytest

from harness.evaluation_contract import DEMONSTRATION_CASES
from harness.llm.client import LLMTimeoutError
from harness.quality_references import load_quality_references
from scripts import calibrate_evaluator_clarity as script
from tests.evaluation_fixtures import EvaluationClient


class LocalClient(EvaluationClient):
    settings = SimpleNamespace(temperature=0, context_size=8192)

    def __init__(self, *args, interrupt_after=None):
        super().__init__(*args)
        self.interrupt_after = interrupt_after

    def generate(self, messages):
        if self.interrupt_after is not None and len(self.requests) >= self.interrupt_after:
            raise KeyboardInterrupt
        return super().generate(messages)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def arrange(monkeypatch, tmp_path, client):
    def factory(environment, **kwargs):
        assert environment == {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": "gemma4:e4b"}
        return client
    monkeypatch.setattr(script, "create_evaluation_client", factory)
    monkeypatch.setattr(script, "frozen_sources", lambda: {"source": "fixed"})
    monkeypatch.setattr(script, "ROOT", tmp_path)


def saved(tmp_path):
    path = next((tmp_path / "outputs/results").glob("evaluator-clarity-expanded-*.json"))
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_preview_has_twelve_new_cases_and_never_creates_client(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("Una vista previa no crea un cliente.")
    monkeypatch.setattr(script, "create_evaluation_client", forbidden)
    assert script.main(["--model", "gemma4:e4b", "--preview"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert len(preview["new_cases"]) >= 10 and preview["planned_evaluations"] == 13
    assert set(preview["new_cases"]).isdisjoint(DEMONSTRATION_CASES)
    assert set(preview["new_cases"]).isdisjoint(script.PREVIOUS_CASES)


@pytest.mark.parametrize("bad", ["E03", "E31"])
def test_selection_refuses_demonstrations_or_reserved_cases(monkeypatch, bad):
    new = script.NEW_CASES[:-1] + (bad,)
    monkeypatch.setattr(script, "NEW_CASES", new)
    monkeypatch.setattr(script, "PLANNED_CASES", script.REGRESSION_CASES + new)
    with pytest.raises(ValueError):
        script.validate_selection({c["case_id"]: c for c in load_quality_references()["cases"]})


def test_full_sample_preserves_inputs_and_records_coverage(monkeypatch, tmp_path):
    client = LocalClient()
    arrange(monkeypatch, tmp_path, client)
    assert script.main(["--model", "gemma4:e4b"]) == 0
    assert len(client.requests) == 13
    _, report = saved(tmp_path)
    assert report["coverage"] == {"planned_new": 12, "evaluated_new": 12, "new_with_valid_analysis": 12, "regression_cases": 1}
    assert report["state"] == "completed" and report["not_executed"] == []
    for messages, row in zip(client.requests, report["cases"], strict=True):
        payload = json.loads(messages[1]["content"])
        assert payload == {"input": row["record"]["request"]}
        assert "expected" not in payload["input"]
        assert row["record"]["few_shot"]["case_ids"] == list(DEMONSTRATION_CASES)
        assert row["clarity_neutrality_review"]["clarity_reason"] is not None


def test_resume_evaluates_only_unfinished_cases(monkeypatch, tmp_path):
    first = LocalClient(interrupt_after=2)
    arrange(monkeypatch, tmp_path, first)
    assert script.main(["--model", "gemma4:e4b"]) == 1
    path, report = saved(tmp_path)
    assert report["state"] == "interrupted" and len(report["cases"]) == 2
    original = report["cases"]
    second = LocalClient()
    arrange(monkeypatch, tmp_path, second)
    assert script.main(["--model", "gemma4:e4b", "--resume", str(path)]) == 0
    assert len(second.requests) == 11
    _, resumed = saved(tmp_path)
    assert resumed["cases"][:2] == original and len(resumed["cases"]) == 13


def test_changed_sources_refuse_resume_before_client_creation(monkeypatch, tmp_path):
    client = LocalClient()
    arrange(monkeypatch, tmp_path, client)
    assert script.main(["--model", "gemma4:e4b"]) == 0
    path, _ = saved(tmp_path)
    monkeypatch.setattr(script, "frozen_sources", lambda: {"source": "changed"})
    def forbidden(*args, **kwargs):
        pytest.fail("No se debe crear un cliente al rechazar fuentes cambiadas.")
    monkeypatch.setattr(script, "create_evaluation_client", forbidden)
    with pytest.raises(SystemExit):
        script.main(["--model", "gemma4:e4b", "--resume", str(path)])


def test_repeated_transport_errors_stop_and_remain_missing_predictions(monkeypatch, tmp_path):
    client = LocalClient([LLMTimeoutError("privado") for _ in range(3)])
    arrange(monkeypatch, tmp_path, client)
    assert script.main(["--model", "gemma4:e4b"]) == 1
    assert len(client.requests) == 3
    _, report = saved(tmp_path)
    assert report["state"] == "stopped_after_technical_errors" and len(report["not_executed"]) == 10
    assert report["coverage"]["new_with_valid_analysis"] == 0
    assert report["new_case_metrics"]["criteria"]["claridad"]["missing_prediction"] == 2
    assert "privado" not in json.dumps(report)

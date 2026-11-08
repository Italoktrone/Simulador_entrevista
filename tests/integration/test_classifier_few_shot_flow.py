"""Trazabilidad few-shot de sesiones y controles públicos sin modelo real."""

import pytest

from harness.session_log import save_session, load_session, SessionLogError
from tests.integration.test_pre_response_classification import make_runtime
from scripts import start_interview


def test_session_records_selection_and_rejects_missing_provenance(tmp_path):
    runtime, _, _ = make_runtime()
    runtime.ask("Describe la utilidad de una herramienta de versiones.")
    runtime.close()
    data = runtime.session_dict()
    metadata = data["interventions"][0]["classification"]["trace"]["llm"]["few_shot"]
    assert metadata["enabled"] and len(metadata["case_ids"]) == 6
    assert load_session(save_session(data, tmp_path / "valid")) == data
    del data["interventions"][0]["classification"]["trace"]["llm"]["few_shot"]
    with pytest.raises(SessionLogError):
        save_session(data, tmp_path / "invalid")


def test_selector_forwards_baseline_switch(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(start_interview, "load_json", lambda _: {"local_model":"modelo", "api_model":"modelo", "api_key":""})
    monkeypatch.setattr("builtins.input", lambda _: "1")
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(start_interview.subprocess, "run", run)
    assert start_interview.main(["--no-classifier-examples"]) == 0
    assert "--no-classifier-examples" in calls[0]

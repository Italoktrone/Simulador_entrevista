"""Evaluador y puntos de control sobre referencias reales, sin conexiones reales."""

import json

import httpx
import pytest

from harness.llm_question_classifier import create_classification_client
from scripts import evaluate_classifier


def load_report(directory):
    files = list(directory.glob("classification-evaluation-*.json"))
    assert len(files) == 1
    return files[0], json.loads(files[0].read_text(encoding="utf-8"))


def test_selected_pilot_runs_only_requested_cases_and_resumes_without_expansion(tmp_path):
    assert evaluate_classifier.main(["--case-id", "R26", "--case-id", "R04", "--case-id", "R08",
        "--output-dir", str(tmp_path)]) == 0
    path, report = load_report(tmp_path)
    assert report["selected_case_ids"] == ["R04", "R08", "R26"]
    assert len(report["cases"]) == 3
    assert report["versions"]["aggregation"] == "1.1.0"
    assert evaluate_classifier.main(["--resume", str(path)]) == 0
    assert len(load_report(tmp_path)[1]["cases"]) == 3
    before = path.read_bytes()
    assert evaluate_classifier.main(["--resume", str(path), "--case-id", "R01"]) == 1
    assert path.read_bytes() == before


@pytest.mark.parametrize("ids", [["R01", "R01"], ["R99"], ["R40"]])
def test_invalid_or_out_of_split_pilot_selection_creates_no_result(ids, tmp_path):
    args = [arg for identifier in ids for arg in ("--case-id", identifier)]
    assert evaluate_classifier.main(args + ["--output-dir", str(tmp_path)]) == 1
    assert list(tmp_path.iterdir()) == []


def test_local_evaluation_runs_all_references_without_a_client_and_preserves_sources(tmp_path, monkeypatch):
    before = evaluate_classifier.source_hashes()
    monkeypatch.setattr(evaluate_classifier, "create_classification_client", lambda *a, **k: pytest.fail("Reglas no usa un cliente"))
    assert evaluate_classifier.main(["--mode", "reglas", "--split", "todos", "--output-dir", str(tmp_path)]) == 0
    _, report = load_report(tmp_path)
    assert report["state"] == "completed" and report["sources_unchanged"]
    assert len(report["cases"]) == report["metrics"]["all"]["n"] == 40
    assert report["metrics"]["desarrollo"]["n"] == 30
    assert report["metrics"]["comprobacion_conocida"]["n"] == 10
    assert report["metrics"]["all"]["llm_generations"] == 0
    assert report["metrics"]["all"]["llm_delegation_rate"]["value"] == 0
    assert report["metrics"]["all"]["local_abstention_rate"]["numerator"] > 0
    assert before == evaluate_classifier.source_hashes()


def test_interrupted_hybrid_resumes_without_repeating_finished_cases_or_using_external_env(tmp_path, monkeypatch):
    calls, clients = [], []
    interrupted = False

    def handler(request):
        nonlocal interrupted
        data = json.loads(json.loads(request.content)["messages"][-1]["content"])["input"]
        assert "expected" not in data and "difficulty" not in data
        calls.append(data["intervention_id"])
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt()
        return httpx.Response(401, text="CUERPO_FICTICIO_NO_REGISTRAR")

    def factory(environ, **kwargs):
        assert environ == {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": "gemma4:e4b"}
        client = create_classification_client(environ, transport=httpx.MockTransport(handler), **kwargs)
        assert client.settings.max_output_tokens == 2048
        clients.append(client)
        return client

    monkeypatch.setenv("LLM_PROVIDER", "unab")
    monkeypatch.setenv("UNAB_API_KEY", "CLAVE_FICTICIA_NO_USAR")
    monkeypatch.setattr(evaluate_classifier, "create_classification_client", factory)
    assert evaluate_classifier.main(["--mode", "hibrido", "--split", "todos", "--output-dir", str(tmp_path)]) == 1
    path, partial = load_report(tmp_path)
    assert partial["state"] == "interrupted" and len(partial["cases"]) < 40
    completed = {entry["case_id"] for entry in partial["cases"]}
    previous_calls = len(calls)
    assert evaluate_classifier.main(["--resume", str(path)]) == 0
    _, final = load_report(tmp_path)
    assert final["state"] == "completed" and len(final["cases"]) == 40
    assert not completed.intersection(calls[previous_calls:])
    assert final["cases"][:len(partial["cases"])] == partial["cases"]
    assert final["metrics"]["all"]["technical_fallback_rate"]["numerator"] > 0
    assert "CUERPO_FICTICIO_NO_REGISTRAR" not in path.read_text(encoding="utf-8")
    assert "CLAVE_FICTICIA_NO_USAR" not in path.read_text(encoding="utf-8")
    assert all(c._http.is_closed for c in clients)
    monkeypatch.setattr(evaluate_classifier, "create_classification_client", lambda *a, **k: pytest.fail("El lote ya terminó"))
    assert evaluate_classifier.main(["--resume", str(path)]) == 0
    unchanged = path.read_bytes()
    assert evaluate_classifier.main(["--resume", str(path), "--model", "gemma4:e2b"]) == 1
    assert path.read_bytes() == unchanged


def test_default_selection_is_development_and_invalid_budget_creates_no_report(tmp_path):
    assert evaluate_classifier.main(["--max-output-tokens", "1", "--output-dir", str(tmp_path)]) == 1
    assert list(tmp_path.iterdir()) == []
    assert evaluate_classifier.main(["--output-dir", str(tmp_path)]) == 0
    _, report = load_report(tmp_path)
    assert len(report["cases"]) == 30
    assert report["execution"]["split"] == "desarrollo"
    assert report["metrics"]["comprobacion_conocida"]["n"] == 0


def test_output_collision_does_not_replace_an_existing_result(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluate_classifier, "uuid4", lambda: "fixed-for-test")
    args = ["--mode", "reglas", "--split", "comprobacion_conocida", "--output-dir", str(tmp_path)]
    assert evaluate_classifier.main(args) == 0
    path, _ = load_report(tmp_path)
    before = path.read_bytes()
    assert evaluate_classifier.main(args) == 1
    assert path.read_bytes() == before


def test_source_change_stops_evaluation_and_marks_the_checkpoint(tmp_path, monkeypatch):
    calls = 0
    def fingerprints():
        nonlocal calls
        calls += 1
        return {"synthetic_source": "before" if calls == 1 else "changed"}
    monkeypatch.setattr(evaluate_classifier, "source_hashes", fingerprints)
    assert evaluate_classifier.main(["--output-dir", str(tmp_path)]) == 1
    _, report = load_report(tmp_path)
    assert report["state"] == "error" and not report["sources_unchanged"]
    assert report["cases"] == []

"""Contrato ampliado y ejecución con el adaptador simulado, sin evaluar un LLM."""

import hashlib
import json
from pathlib import Path

import httpx

from harness.llm.factory import create_client
from harness.reference_cases import DEFAULT_SUITE_PATH, load_reference_suite
from harness.session_log import load_session
from scripts import run_reference_cases


EXTENDED = DEFAULT_SUITE_PATH.with_name("consistencia_ampliada.json")


def test_extended_contract_covers_remaining_cases_with_references_to_real_sources():
    suite = load_reference_suite(EXTENDED)
    cases = suite.resolved_cases()
    assert len(cases) == 6 and sum(len(c["steps"]) for c in cases) == 10
    assert [len(c["steps"]) for c in cases] == [2, 2, 1, 1, 2, 2]
    assert [f["value"] for f in cases[0]["reference_facts"]] == ["2025-04", "2025-08", "2025-11", "2025-12", "2026-09"]
    assert cases[1]["reference_facts"][0]["value"] == ["Python", "Flask", "PostgreSQL", "Git", "pytest"]
    assert cases[3]["reference_facts"][1]["value"] == ["No tuvo clientes comerciales.", "No tuvo operación real en producción."]
    assert cases[4]["steps"][0]["question"] == cases[4]["steps"][1]["question"]
    assert all(f["criterion"] == "consistency_constraint" for f in cases[2]["reference_facts"])
    assert len(load_reference_suite().resolved_cases()) == 4


def test_extended_batch_uses_exact_questions_and_isolates_all_six_sessions(monkeypatch, tmp_path):
    output = tmp_path / "results"
    monkeypatch.setattr(run_reference_cases, "RESULTS_DIR", output)
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(200, json={"model": "gemma4:e4b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": "Respuesta simulada; no es evidencia semántica"}})

    clients = []

    def factory(values):
        client = create_client(values, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client

    monkeypatch.setattr(run_reference_cases, "create_client", factory)
    assert run_reference_cases.main(["--suite", str(EXTENDED), "--model", "gemma4:e4b"]) == 0
    report = json.loads(next(output.glob("reference-run-*.json")).read_text(encoding="utf-8"))
    assert report["suite_source_sha256"] == hashlib.sha256(EXTENDED.read_bytes()).hexdigest().upper()
    assert report["technical_status"] == "completed" and report["semantic_review"] == "pending_human_review"
    assert len(set(c["session_id"] for c in report["cases"])) == 6 and report["sources_unchanged"]
    assert [len(p["messages"]) for p in requests] == [2, 4, 2, 4, 2, 2, 2, 4, 2, 4]
    planned = [step["question"] for c in load_reference_suite(EXTENDED).resolved_cases() for step in c["steps"]]
    assert [p["messages"][-1]["content"] for p in requests] == planned
    for case in report["cases"]:
        session = load_session(case["session_file"])
        assert session == case["session_snapshot"] and session["source_integrity"] == "unchanged"
        assert len(session["attempts"]) == case["expected_steps"]
        assert all(a["status"] == "completed" for a in session["attempts"])
    assert clients[0]._http.is_closed

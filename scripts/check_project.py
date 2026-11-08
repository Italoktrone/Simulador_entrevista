"""Comprobaciones de entrega, informes técnicos y evaluación documental sin LLM."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
# Ejecutar únicamente módulos locales conocidos, sin intérprete de comandos.
import subprocess  # nosec B404
import sys
from tempfile import TemporaryDirectory

from app.contracts import RunInput, RunOutput, SessionInput
from harness.document_search import DocumentSearch
from harness.interview_config import load_interview_setup
from harness.json_loader import load_json


ROOT = Path(__file__).resolve().parents[1]


def evaluate_retrieval():
    search = DocumentSearch.from_setup(load_interview_setup())
    cases = load_json(ROOT / "data/reference_questions/rag_basica.json")["cases"]
    results = []
    for case in cases:
        found = search.search(case["query"])
        identifiers = [item["document_id"] for item in found]
        passed = case["expected_document"] in identifiers if case["expected_document"] else not identifiers
        results.append({"id": case["id"], "passed": passed, "retrieved": identifiers})
    return {"kind": "retrieval_only", "model_calls": 0, "cases": results,
            "passed": sum(case["passed"] for case in results), "total": len(results)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args(argv)
    directory = args.reports_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    for name, model in (("input", RunInput), ("output", RunOutput), ("session", SessionInput)):
        expected = model.model_json_schema()
        if load_json(ROOT / f"agent/{name}.schema.json") != expected:
            print(f"Contrato desactualizado: agent/{name}.schema.json")
            return 1
    with TemporaryDirectory(prefix="quality-", dir=directory) as temporary:
        commands = {
            "pytest": [sys.executable, "-B", "-m", "pytest", "-q", "--tb=short", "--basetemp", str(Path(temporary) / "pytest"), "--junitxml", str(directory / "pytest.xml")],
            "ruff": [sys.executable, "-B", "-m", "ruff", "check", "--no-cache", "--output-format", "json", "app", "harness", "scripts", "tests"],
            "bandit": [sys.executable, "-B", "-m", "bandit", "-r", "app", "harness", "scripts", "-f", "json"],
        }
        checks = {}
        for name, command in commands.items():
            environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
            result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8")  # nosec B603
            (directory / f"{name}.{'txt' if name == 'pytest' else 'json'}").write_text(result.stdout, encoding="utf-8")
            checks[name] = {"exit_code": result.returncode}
            print(f"{name}: {result.returncode}", flush=True)
            if result.returncode:
                print(result.stdout[-5000:])
                print(result.stderr[-2000:])
    retrieval = evaluate_retrieval()
    (directory / "rag-evaluation.json").write_text(json.dumps(retrieval, indent=2), encoding="utf-8")
    summary = {"timestamp": datetime.now(timezone.utc).isoformat(), "python": sys.version,
               "checks": checks, "retrieval": retrieval}
    (directory / "quality-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return int(any(item["exit_code"] for item in checks.values()) or retrieval["passed"] != retrieval["total"])


if __name__ == "__main__":
    raise SystemExit(main())

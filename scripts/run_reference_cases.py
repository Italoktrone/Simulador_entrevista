"""Ejecutar las referencias en Ollama local, sin puntuar ni juzgar respuestas."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from harness.interview_config import load_interview_setup
from harness.llm.client import LLMError
from harness.llm.config import OllamaSettings
from harness.llm.factory import create_client
from harness.profile import ProfileIntegrityError
from harness.prompt_builder import load_instructions
from harness.reference_cases import DEFAULT_SUITE_PATH, load_reference_suite
from harness.runtime import InterviewRuntime
from harness.session_log import SessionLogError, save_session
from harness.session_state import describe_issue


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "outputs/results"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE_PATH)
    parser.add_argument("--model", help="Modelo local; si se omite usa OLLAMA_MODEL o el predeterminado.")
    args = parser.parse_args(argv)
    report = {
        "batch_version": "1.0.0", "run_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "technical_status": "error", "semantic_review": "pending_human_review",
        "cases": [], "issues": [],
    }
    # Una huella no es una revisión semántica; sirve para conservar procedencia.
    sources = [ROOT / p for p in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]
    output = RESULTS_DIR / f"reference-run-{report['run_id']}.json"
    code = 1
    try:
        setup = load_interview_setup()
        suite = load_reference_suite(args.suite, setup=setup)
        instructions = load_instructions()
        definitions = suite.resolved_cases()
        report.update(
            suite_id=suite.suite_id, suite_source_sha256=suite.source_sha256,
            suite_definition=suite.to_dict(), reference_cases=definitions,
            source_hashes_before={str(p): _hash(p) for p in sources},
            runner_source_sha256=_hash(Path(__file__)),
        )
        # Este comando es una prueba local incluso si el entorno selecciona API.
        model = args.model if args.model is not None else os.environ.get("OLLAMA_MODEL", OllamaSettings().model)
        with create_client({"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": model}) as client:
            report.update(provider=client.provider, settings=asdict(client.settings))
            print(f"REFERENCIAS REALES. Ollama local: {client.settings.model}.", flush=True)
            print(f"Casos: {len(definitions)}. Revisión humana pendiente.", flush=True)
            for definition in definitions:
                runtime = InterviewRuntime(setup, instructions, client, provider=client.provider, model=client.settings.model)
                entry = {"case_id": definition["case_id"], "session_id": runtime.session_id, "session_file": None}
                report["cases"].append(entry)
                problem = None
                print(f"\n{definition['case_id']}", flush=True)
                try:
                    for step in definition["steps"]:
                        print(f"  P{step['step_number']}: {step['question']}", flush=True)
                        result = runtime.ask(step["question"])
                        print(f"  Candidato: {result.text}\n  Tiempo: {result.elapsed_seconds:.2f} s", flush=True)
                except (LLMError, ProfileIntegrityError, KeyboardInterrupt) as error:
                    problem = error
                    report["issues"].append(describe_issue(error))
                    print(f"  Detenido: {describe_issue(error)['message']}", flush=True)
                finally:
                    try:
                        runtime.assert_source_unchanged()
                    except ProfileIntegrityError as error:
                        problem = error
                        issue = describe_issue(error)
                        if issue not in report["issues"]:
                            report["issues"].append(issue)
                    runtime.close("interrupted" if isinstance(problem, KeyboardInterrupt) else "closed")
                    snapshot = runtime.session_dict()
                    entry.update(
                        session_snapshot=snapshot,
                        attempt_statuses=[a["status"] for a in snapshot["attempts"]],
                        expected_steps=len(definition["steps"]),
                    )
                    # Si falla el guardado, el informe final conserva la copia.
                    session_file = save_session(snapshot)
                    entry.update(session_file=str(session_file), session_sha256=_hash(session_file))
                if problem is not None:
                    report["technical_status"] = "interrupted" if isinstance(problem, KeyboardInterrupt) else "error"
                    break
            else:
                report["technical_status"] = "completed"
                code = 0
    except KeyboardInterrupt as error:
        code = 1
        report["technical_status"] = "interrupted"
        report["issues"].append(describe_issue(error))
    except (ValueError, LLMError, SessionLogError, OSError) as error:
        code = 1
        # No copiar cuerpos de proveedor, preguntas inválidas o secretos.
        report["issues"].append(describe_issue(error))
        report["technical_status"] = "error"
        print("No se completó el lote. Se conservará la evidencia disponible.", flush=True)
    finally:
        if "source_hashes_before" in report:
            try:
                report["source_hashes_after"] = {str(p): _hash(p) for p in sources}
                report["sources_unchanged"] = report["source_hashes_before"] == report["source_hashes_after"]
            except OSError:
                report["sources_unchanged"] = False
            if not report["sources_unchanged"]:
                report["technical_status"] = "error"
                code = 1
        planned = [c["case_id"] for c in report.get("reference_cases", [])]
        started = {c["case_id"] for c in report["cases"]}
        report["not_executed_case_ids"] = [identifier for identifier in planned if identifier not in started]
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8", newline="\n") as target:
                json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
                target.write("\n")
        except OSError:
            print("No se pudo guardar el informe del lote. Revisa las sesiones ya guardadas.", flush=True)
            code = 1
        else:
            print(f"\nEvidencia: {output}", flush=True)
    print(f"Estado técnico: {report['technical_status']}. La consistencia requiere revisión humana.", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

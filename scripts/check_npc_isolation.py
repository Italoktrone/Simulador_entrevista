"""Comprobar preguntas conocidas en los tres NPC con Ollama; revisión semántica aparte."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
from pathlib import Path
import subprocess  # nosec B404
import shutil
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import create_app
from harness.candidate_catalog import CANDIDATES, load_candidate_setup
from harness.llm.config import OllamaSettings
from harness.session_log import load_session
from harness.behavioral_evidence import select_support_evidence, audit_support_selection


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/reference_questions/aislamiento_npcs.json"
SUPPORT_DATASET = ROOT / "data/reference_questions/apoyo_npcs.json"


def source_hashes():
    files = ["agent/agent.md", "agent/manifest.yaml", "harness/prompt_builder.py",
             "harness/document_search.py", "harness/response_validator.py", "harness/runtime.py",
             "harness/llm/ollama_client.py", "data/jobs/desarrollador_junior.json",
             "data/reference_questions/aislamiento_npcs.json", "data/reference_questions/apoyo_npcs.json",
             "harness/behavioral_evidence.py", "scripts/check_npc_isolation.py", "app/service.py"]
    files += [path for paths in CANDIDATES.values() for path in paths]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemma4:e4b")
    parser.add_argument("--questions", nargs="+", help="IDs del conjunto; por defecto las trece preguntas")
    parser.add_argument("--suite", choices=("isolation", "support"), default="isolation")
    parser.add_argument("--candidates", nargs="+", choices=tuple(CANDIDATES), default=tuple(CANDIDATES))
    parser.add_argument("--with-history", action="store_true", help="Añadir tres turnos seguidos por candidato")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "reports/npc-isolation")
    args = parser.parse_args(argv)
    dataset_path = SUPPORT_DATASET if args.suite == "support" else DATASET
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    ids = {q["id"] for q in dataset["questions"]}
    if args.questions and not set(args.questions) <= ids:
        parser.error("ID de pregunta desconocido.")
    questions = [q for q in dataset["questions"] if not args.questions or q["id"] in args.questions]
    directory = args.reports_dir.resolve() / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    report_path = directory / "responses.json"
    git = shutil.which("git")
    commit = subprocess.run([git, "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True,
                            text=True).stdout.strip() if git else None  # nosec B603
    report = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "commit": commit,
              "method": {"api": "FastAPI ASGI en proceso; adaptador Ollama HTTP real",
                         "model": args.model, "classify": False, "evaluate": False, "use_rag": True,
                         "repetitions_per_case": 1, "settings": asdict(OllamaSettings(model=args.model)),
                         "suite": args.suite, "candidates": args.candidates,
                         "independent_questions": [q["id"] for q in questions],
                         "with_history": args.with_history},
              "source_hashes_before": source_hashes(), "cases": [], "sessions": [],
              "semantic_review": "Pendiente de cotejo con perfiles; no hay aprobación educativa automática."}

    def save():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def run_session(client, candidate_id, sequence, case_type):
        created = client.post("/sessions", json={"request_id": str(uuid4()), "candidate_id": candidate_id,
                                                "classify": False, "evaluate": False})
        created.raise_for_status()
        identifier = created.json()["session_id"]
        history = []
        profile = load_candidate_setup(candidate_id).candidate.to_dict()
        for definition in sequence:
            if source_hashes() != report["source_hashes_before"]:
                raise RuntimeError("Las fuentes cambiaron durante el ensayo.")
            entry = {"candidate_id": candidate_id, "question_id": definition["id"],
                     "question": definition["question"], "session_id": identifier,
                     "case_type": case_type, "request_id": str(uuid4()), "status": "pending"}
            entry["expectation"] = definition.get("expectation", definition.get("expected_by_candidate", {}).get(candidate_id))
            entry["behavioral_selection_expected"] = audit_support_selection(select_support_evidence(profile, entry["question"], history))
            report["cases"].append(entry)
            save()
            response = client.post("/run", json={"session_id": identifier, "request_id": entry["request_id"],
                                                 "question": entry["question"], "use_rag": True})
            response.raise_for_status()
            entry.update(status=response.json()["status"], result=response.json())
            events = client.get("/logs", params={"session_id": identifier})
            events.raise_for_status()
            finished = [e for e in events.json()["events"] if e["event"] == "run_finished" and e["run_id"] == entry["request_id"]]
            if len(finished) != 1 or finished[0]["behavioral_selection"] != entry["behavioral_selection_expected"]:
                raise RuntimeError("El registro del turno no conserva la selección esperada.")
            entry["behavioral_selection_logged"] = finished[0]["behavioral_selection"]
            if entry["status"] == "completed":
                history.extend([{"role": "user", "content": entry["question"]}, {"role": "assistant", "content": entry["result"]["reply"]}])
            save()
            print(f"{len(report['cases']):02} {candidate_id} {case_type} {definition['id']}: {entry['status']}", flush=True)
        client.post(f"/sessions/{identifier}/close").raise_for_status()
        saved = directory / "api/sessions" / f"session-{identifier}.json"
        session = load_session(saved)
        if session["candidate_id"] != candidate_id or len(session["attempts"]) != len(sequence):
            raise RuntimeError("La sesión no conserva el perfil y los intentos esperados.")
        report["sessions"].append({"session_id": identifier, "candidate_id": candidate_id,
                                   "file": str(saved.relative_to(directory)), "attempts": len(session["attempts"]),
                                   "sha256": hashlib.sha256(saved.read_bytes()).hexdigest()})
        save()

    os.environ.update(LLM_PROVIDER="ollama", LLM_ALLOW_EXTERNAL_API="false", OLLAMA_MODEL=args.model)
    api_token = secrets.token_urlsafe(32)
    application = create_app(directory=directory / "api", token=api_token)
    save()
    print(f"Evidencia: {report_path}", flush=True)
    try:
        with TestClient(application, headers={"Authorization": "Bearer " + api_token}) as client:
            for candidate_id in args.candidates:
                load_candidate_setup(candidate_id).candidate.assert_source_unchanged()
                for question in questions:
                    run_session(client, candidate_id, [question], "independent")
                if args.with_history:
                    run_session(client, candidate_id, dataset["continuity"], "continuity")
    finally:
        report["source_hashes_after"] = source_hashes()
        report["sources_unchanged"] = report["source_hashes_before"] == report["source_hashes_after"]
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        save()
    return int(not report["sources_unchanged"] or any(c["status"] != "completed" for c in report["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())

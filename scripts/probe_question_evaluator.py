"""Piloto local acotado sobre contexto original, sin candidato ni clasificador."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.session_log import load_session


def main(argv=None):
    parser = argparse.ArgumentParser(description="Comprobar hasta dos intervenciones con el evaluador local.")
    parser.add_argument("--session", required=True)
    parser.add_argument("--intervention", action="append", type=int, required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args(argv)
    if not 1 <= len(args.intervention) <= 2 or len(set(args.intervention)) != len(args.intervention):
        parser.error("Selecciona una o dos intervenciones distintas.")
    source = Path(args.session)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    session = load_session(source)
    records = session.get("evaluations", [])
    if any(not 1 <= n <= len(records) or records[n-1]["question_number"] is None for n in args.intervention):
        parser.error("Las intervenciones deben tener una pregunta enviada y contexto de evaluación registrado.")
    run_id = str(uuid4())
    output = Path(__file__).resolve().parents[1] / "outputs/results" / ("evaluator-local-probe-" + run_id + ".json")
    report = {"probe_version": "1.0.0", "source_session_id": session["session_id"], "source_sha256": before,
              "model": args.model, "provider": "ollama", "semantic_review": "pending_human_review",
              "scope": "component_only_original_context_no_candidate_or_classifier", "state": "running", "cases": []}
    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        # Entorno explícito local. No se consulta la configuración privada ni se
        # hereda un proveedor externo o sus credenciales.
        env = {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model}
        with create_evaluation_client(env) as client:
            evaluator = QuestionEvaluator(client)
            report["rubric"] = evaluator.rubric
            for number in args.intervention:
                previous = records[number-1]
                record = evaluator.evaluate(deepcopy(previous["request"]), session_id=run_id,
                                            intervention_id=f"{run_id}:i{number}", question_number=previous["question_number"])
                report["cases"].append({"intervention_number": number,
                    "previous_status": previous["status"], "previous_seconds": previous["elapsed_seconds"],
                    "previous_levels": None if previous["analysis"] is None else {k: v["level"] for k,v in previous["analysis"]["criteria"].items()},
                    "record": record})
                save()
                print(json.dumps({"intervention": number, "status": record["status"], "reason": record["reason_code"],
                                  "seconds": round(record["elapsed_seconds"], 2), "attempts": len(record["attempts"]),
                                  "levels": None if record["analysis"] is None else {k:v["level"] for k,v in record["analysis"]["criteria"].items()}}, ensure_ascii=False), flush=True)
        report["state"] = "completed"
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except Exception:
        report["state"] = "error"
    finally:
        report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == before
        save()
    print("Informe:", output, flush=True)
    return 0 if report["state"] == "completed" and report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

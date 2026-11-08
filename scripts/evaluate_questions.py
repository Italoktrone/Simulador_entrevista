"""Vista previa sin modelo y comparación de referencias revisadas explícitamente."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.interview_config import load_interview_setup
from harness.quality_references import REFERENCE_PATH, load_quality_references, compare_quality, quality_metrics
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.scoring import CONFIG_PATH, load_rubric


def main(argv=None):
    parser = argparse.ArgumentParser(description="Revisar o evaluar referencias educativas.")
    parser.add_argument("--preview", action="store_true", help="Mostrar propuestas sin crear clientes ni consultar modelos")
    parser.add_argument("--references", default=str(REFERENCE_PATH))
    parser.add_argument("--evaluation-config", default=str(CONFIG_PATH))
    parser.add_argument("--split", choices=["desarrollo", "comprobacion_conocida", "todos"], default="desarrollo")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--model")
    parser.add_argument("--no-evaluator-examples", action="store_true", help="Comparar sin las seis demostraciones")
    args = parser.parse_args(argv)
    rubric = load_rubric(args.evaluation_config)
    suite = load_quality_references(args.references, rubric=rubric)
    if set(args.case_id) - {c["case_id"] for c in suite["cases"]}:
        parser.error("Hay identificadores de caso desconocidos.")
    cases = [c for c in suite["cases"] if (args.split == "todos" or c["split"] == args.split)
             and (not args.case_id or c["case_id"] in args.case_id)]
    if not cases:
        parser.error("La selección no contiene casos.")
    if args.preview:
        for case in cases:
            print(f"{case['case_id']} [{case['review_status']}] {case['question']!r}")
            print("  Propuesta:", case["expected"]["levels"], "=>", case["expected"]["visible_level"] or case["expected"]["status"])
        print(f"{len(cases)} propuestas. Sin llamadas al modelo. Revisa también las justificaciones del JSON.")
        return 0
    pending = [c["case_id"] for c in cases if c["review_status"] != "approved"]
    if pending:
        print("No se ejecutó el modelo. Faltan referencias revisadas y aprobadas: " + ", ".join(pending))
        return 2
    setup = load_interview_setup()
    identifier = str(uuid4())
    sources = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (args.references, args.evaluation_config)}
    report = {"report_version": "1.0.0", "run_id": identifier, "rubric": rubric, "split": args.split,
              "source_hashes": sources, "state": "running", "cases": [], "metrics": quality_metrics([])}
    output = Path(__file__).resolve().parents[1] / "outputs/results" / ("question-evaluation-" + identifier + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        with create_evaluation_client(rubric=rubric, model=args.model) as client:
            evaluator = QuestionEvaluator(client, rubric=rubric, few_shot=not args.no_evaluator_examples)
            for case in cases:
                request = {"question": case["question"], "configuration": setup.config_dict() | {"approach": case["approach"]},
                           "job": setup.job_dict(), "competency": case["competency"], "objective": case["objective"],
                           "context_turns": case["context_turns"], "classification": case["classification"]}
                record = evaluator.evaluate(request, session_id=identifier, intervention_id=identifier + ":" + case["case_id"])
                comparison = compare_quality(case["expected"], record)
                report["cases"].append({"case_id": case["case_id"], "expected": case["expected"], "record": record, **comparison})
                report["metrics"] = quality_metrics(report["cases"])
                save()
                print(case["case_id"], record["status"], "coincide" if comparison["exact"] else "requiere revisión")
        report["state"] = "completed"
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except Exception:
        report["state"] = "error"
        print("Ejecución detenida; se conservan los resultados terminados sin copiar detalles privados del error.")
    finally:
        report["sources_unchanged"] = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == v for p, v in sources.items())
        save()
    print("Informe:", output)
    return 0 if report["state"] == "completed" and report["sources_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

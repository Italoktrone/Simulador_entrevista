"""Calibración local: doce casos nuevos fuera de las demostraciones y E11."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.evaluation_contract import DEMONSTRATION_CASES, validate_record
from harness.interview_config import load_interview_setup
from harness.json_loader import load_json
from harness.quality_references import load_quality_references, compare_quality, quality_metrics
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.scoring import load_rubric
from scripts.calibrate_evaluator_few_shot import case_request, source_hashes

ROOT = Path(__file__).resolve().parents[1]
NEW_CASES = ("E01", "E04", "E09", "E10", "E17", "E18", "E19", "E24", "E25", "E26", "E28", "E30")
PREVIOUS_CASES = ("E05", "E07", "E08", "E11")
REGRESSION_CASES = ("E11",)
PLANNED_CASES = REGRESSION_CASES + NEW_CASES


def frozen_sources():
    result = source_hashes()
    for path in ("scripts/calibrate_evaluator_clarity.py", "scripts/calibrate_evaluator_few_shot.py"):
        result[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    return result


def validate_selection(cases):
    if (PLANNED_CASES != REGRESSION_CASES + NEW_CASES or len(NEW_CASES) < 10
            or len(set(PLANNED_CASES)) != len(PLANNED_CASES)
            or set(NEW_CASES) & set(PREVIOUS_CASES)
            or set(PLANNED_CASES) & set(DEMONSTRATION_CASES)):
        raise ValueError("La muestra debe contener diez o más casos nuevos fuera de las demostraciones.")
    if any(i not in cases or cases[i]["split"] != "desarrollo" or cases[i]["review_status"] != "approved"
           for i in PLANNED_CASES):
        raise ValueError("La muestra requiere solo referencias de desarrollo aprobadas.")


def update_metrics(report):
    report["metrics"] = quality_metrics(report["cases"])
    new = [c for c in report["cases"] if c["role"] == "new_development"]
    report["new_case_metrics"] = quality_metrics(new)
    report["coverage"] = {"planned_new": len(NEW_CASES), "evaluated_new": len(new),
                          "new_with_valid_analysis": sum(c["record"]["analysis"] is not None for c in new),
                          "regression_cases": len(report["cases"]) - len(new)}


def validate_resume(report, args, cases, setup, rubric, hashes):
    if (report.get("calibration_version") != "1.0.0" or report.get("model") != args.model
            or report.get("provider") != "ollama" or report.get("source_hashes") != hashes
            or report.get("rubric") != rubric or report.get("planned_cases") != list(PLANNED_CASES)):
        raise ValueError("No se puede reanudar con otro modelo, selección, prompt o fuentes.")
    done = report.get("cases")
    if not isinstance(done, list) or [c.get("case_id") for c in done] != list(PLANNED_CASES[:len(done)]):
        raise ValueError("El orden de los casos guardados no corresponde a la muestra.")
    if report.get("not_executed") != list(PLANNED_CASES[len(done):]):
        raise ValueError("Los casos pendientes no corresponden al registro guardado.")
    for row in done:
        case = cases[row["case_id"]]
        record = validate_record(row["record"], rubric)
        if record["request"] != case_request(case, setup) or row["expected"] != case["expected"]:
            raise ValueError("Una entrada o expectativa guardada no coincide con la referencia.")
        if row["role"] != ("regression" if row["case_id"] in REGRESSION_CASES else "new_development"):
            raise ValueError("El rol del caso guardado no coincide con la muestra.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--preview", action="store_true", help="Mostrar muestra sin crear cliente")
    parser.add_argument("--resume", help="Continuar solo casos pendientes de un informe con fuentes idénticas")
    args = parser.parse_args(argv)
    rubric = load_rubric()
    cases = {c["case_id"]: c for c in load_quality_references(rubric=rubric)["cases"]}
    setup = load_interview_setup()
    try:
        validate_selection(cases)
    except ValueError as error:
        parser.error(str(error))
    if args.preview:
        print(json.dumps({"new_cases": NEW_CASES, "regression_cases": REGRESSION_CASES,
                          "excluded_demonstrations": DEMONSTRATION_CASES, "planned_evaluations": len(PLANNED_CASES),
                          "provider": "ollama", "model_calls": 0}, ensure_ascii=False))
        return 0
    hashes = frozen_sources()
    if args.resume:
        output = Path(args.resume)
        report = load_json(output)
        try:
            validate_resume(report, args, cases, setup, rubric, hashes)
        except ValueError as error:
            parser.error(str(error))
    else:
        identifier = str(uuid4())
        output = ROOT / "outputs/results" / ("evaluator-clarity-expanded-" + identifier + ".json")
        report = {"calibration_version": "1.0.0", "run_id": identifier, "state": "running",
                  "scope": "known_approved_development_outside_demonstrations_not_blind_validation",
                  "provider": "ollama", "model": args.model, "rubric": rubric, "source_hashes": hashes,
                  "planned_cases": list(PLANNED_CASES), "new_cases": list(NEW_CASES),
                  "regression_cases": list(REGRESSION_CASES), "cases": [], "not_executed": list(PLANNED_CASES),
                  "limits": {"read_timeout_seconds": rubric["read_timeout_seconds"],
                             "max_output_tokens": rubric["max_output_tokens"], "transport_retries": 0,
                             "generations_per_case": 2, "stop_after_consecutive_technical_failures": 3}}
        output.parent.mkdir(parents=True, exist_ok=True)
        # Nunca sobrescribir otro ensayo al iniciar uno nuevo.
        with output.open("x", encoding="utf-8") as target:
            json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
    def save():
        update_metrics(report)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Informe:", output, flush=True)
    if not report["not_executed"]:
        return 0 if report["state"] == "completed" else 1
    report["state"] = "running"
    save()
    consecutive_failures = 0
    try:
        environment = {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model}
        with create_evaluation_client(environment, rubric=rubric) as client:
            report["temperature"] = client.settings.temperature
            report["context_size"] = client.settings.context_size
            evaluator = QuestionEvaluator(client, rubric=rubric, few_shot=True)
            for case_id in list(report["not_executed"]):
                if frozen_sources() != hashes:
                    report["state"] = "sources_changed"
                    break
                case = cases[case_id]
                record = evaluator.evaluate(case_request(case, setup), session_id=report["run_id"],
                                            intervention_id=report["run_id"] + ":" + case_id)
                report["cases"].append({"case_id": case_id,
                    "role": "regression" if case_id in REGRESSION_CASES else "new_development",
                    "expected": deepcopy(case["expected"]), "record": record,
                    "clarity_neutrality_review": {"status": "pending_review",
                        "clarity_reason": None if record["analysis"] is None else record["analysis"]["criteria"]["claridad"]["reason"],
                        "neutrality_reason": None if record["analysis"] is None else record["analysis"]["criteria"]["neutralidad"]["reason"]},
                    **compare_quality(case["expected"], record)})
                report["not_executed"].remove(case_id)
                save()
                print(json.dumps({"case_id": case_id, "status": record["status"],
                    "levels": None if record["analysis"] is None else {k: v["level"] for k, v in record["analysis"]["criteria"].items()},
                    "exact": report["cases"][-1]["exact"], "seconds": round(record["elapsed_seconds"], 2),
                    "attempts": len(record["attempts"]), "remaining": len(report["not_executed"])}, ensure_ascii=False), flush=True)
                technical = record["analysis"] is None and record["attempts"][-1]["status"] != "validada"
                consecutive_failures = consecutive_failures + 1 if technical else 0
                if consecutive_failures >= 3:
                    report["state"] = "stopped_after_technical_errors"
                    break
        if report["state"] == "running":
            report["state"] = "completed"
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except Exception:
        report["state"] = "error"
    finally:
        report["sources_unchanged"] = frozen_sources() == hashes
        if not report["sources_unchanged"]:
            report["state"] = "sources_changed"
        save()
    return 0 if report["state"] == "completed" and report["sources_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

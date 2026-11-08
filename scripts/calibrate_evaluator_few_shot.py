"""A/B local acotado: dos demostraciones conocidas y un caso de transferencia."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.evaluation_contract import DEMONSTRATION_CASES
from harness.interview_config import load_interview_setup
from harness.quality_references import load_quality_references, compare_quality, quality_metrics
from harness.question_evaluator import QuestionEvaluator, create_evaluation_client
from harness.scoring import load_rubric

ROOT = Path(__file__).resolve().parents[1]
TARGET_CASES = ("E05", "E07", "E11")
FROZEN_SOURCES = ("config/evaluation.json", "config/evaluator_few_shot.json",
    "config/interviews/basica.json", "data/jobs/desarrollador_junior.json", "harness/llm/ollama_client.py",
    "data/reference_questions/evaluacion_calidad_aprobada.json", "data/reference_questions/evaluator_demonstrations.json",
    "agent/evaluator.md", "harness/scoring.py", "harness/feedback.py", "harness/evaluation_contract.py",
    "harness/evaluator_few_shot.py", "harness/question_evaluator.py", "harness/quality_references.py")


def source_hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FROZEN_SOURCES}


def case_request(case, setup):
    return deepcopy({"question": case["question"], "configuration": setup.config_dict() | {"approach": case["approach"]},
                     "job": setup.job_dict(), "competency": case["competency"], "objective": case["objective"],
                     "context_turns": case["context_turns"], "classification": case["classification"]})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--preview", action="store_true", help="Inspeccionar el contraste sin crear cliente")
    args = parser.parse_args(argv)
    rubric = load_rubric()
    suite = load_quality_references(rubric=rubric)
    cases = {c["case_id"]: c for c in suite["cases"]}
    if any(cases[i]["review_status"] != "approved" or cases[i]["split"] != "desarrollo" for i in TARGET_CASES):
        parser.error("El contraste requiere tres referencias de desarrollo aprobadas.")
    setup = load_interview_setup()
    if args.preview:
        class NoGeneration:
            def generate(self, *args, **kwargs):
                raise AssertionError("La vista previa no genera respuestas.")
        for mode in (False, True):
            evaluator = QuestionEvaluator(NoGeneration(), rubric=rubric, few_shot=mode)
            system, metadata = evaluator._prompt_for(case_request(cases["E05"], setup))
            print(json.dumps({"mode": "few_shot" if mode else "baseline", "system_characters": len(system),
                              "demonstrations": metadata["case_ids"], "targets": TARGET_CASES,
                              "planned_comparisons": 6, "model_calls": 0}, ensure_ascii=False))
        return 0
    sources = source_hashes()
    identifier = str(uuid4())
    output = ROOT / "outputs/results" / ("evaluator-few-shot-ab-" + identifier + ".json")
    report = {"calibration_version": "1.0.0", "run_id": identifier, "state": "running",
              "scope": "known_development_imitation_and_one_transfer_case_not_blind_accuracy",
              "model": args.model, "provider": "ollama", "rubric": rubric, "source_hashes": sources,
              "targets": list(TARGET_CASES), "cases": [],
              "not_executed": [[mode, i] for i in TARGET_CASES for mode in ("baseline", "few_shot")],
              "limits": {"max_output_tokens": rubric["max_output_tokens"], "read_timeout_seconds": rubric["read_timeout_seconds"],
                         "generations_per_case": 2, "planned_comparisons": 6, "transport_retries": 0}}
    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        environment = {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model}
        with create_evaluation_client(environment, rubric=rubric) as client:
            report["temperature"] = client.settings.temperature
            report["context_size"] = client.settings.context_size
            evaluators = {mode: QuestionEvaluator(client, rubric=rubric, few_shot=mode == "few_shot") for mode in ("baseline", "few_shot")}
            for case_id in TARGET_CASES:
                case = cases[case_id]
                request = case_request(case, setup)
                for mode, evaluator in evaluators.items():
                    record = evaluator.evaluate(deepcopy(request), session_id=identifier, intervention_id=identifier + ":" + case_id + ":" + mode)
                    comparison = compare_quality(case["expected"], record)
                    report["cases"].append({"case_id": case_id, "mode": mode, "expected": deepcopy(case["expected"]),
                                            "target_in_demonstration_set": case_id in DEMONSTRATION_CASES,
                                            "record": record, **comparison})
                    report["not_executed"].remove([mode, case_id])
                    save()
                    print(json.dumps({"case_id": case_id, "mode": mode, "status": record["status"], "exact": comparison["exact"],
                                      "levels": None if record["analysis"] is None else {k: v["level"] for k, v in record["analysis"]["criteria"].items()},
                                      "reason": record["reason_code"], "seconds": round(record["elapsed_seconds"], 2),
                                      "attempts": len(record["attempts"])}, ensure_ascii=False), flush=True)
                    if record["analysis"] is None and record["attempts"][-1]["status"] != "validada":
                        report["state"] = "stopped_on_technical_error"
                        break
                if report["state"] != "running":
                    break
        if report["state"] == "running":
            report["state"] = "completed"
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except Exception:
        report["state"] = "error"
    finally:
        report["sources_unchanged"] = source_hashes() == sources
        report["metrics"] = {mode: quality_metrics([c for c in report["cases"] if c["mode"] == mode]) for mode in ("baseline", "few_shot")}
        save()
    print("Informe:", output, flush=True)
    return 0 if report["state"] == "completed" and report["sources_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

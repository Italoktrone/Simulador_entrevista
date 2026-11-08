"""Contraste local A/B de tres discrepancias conocidas, sin modificar referencias."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.classifier_few_shot import load_few_shot
from harness.intervention_log import select_classification_context
from harness.llm_question_classifier import LLMQuestionClassifier, create_classification_client
from harness.response_policy import decide_response
from harness.session_log import load_session

TARGETS = {
    2: {"approaches": ["situacional"], "forms": ["abierta"], "attributes": []},
    6: {"approaches": ["situacional"], "forms": ["abierta"], "attributes": []},
    10: {"approaches": ["factual_tecnico"], "forms": ["cerrada"], "attributes": []},
}


def compare_prediction(result, expected):
    if result["technical_error"] is not None or result["evaluability"] != "evaluable":
        return {"semantic_match": False, "differences": ["sin_clasificacion_evaluable"]}
    labels = result["classification"]
    differences = [key for key, values in expected.items() if set(labels[key]) != set(values)]
    return {"semantic_match": not differences, "differences": differences}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args(argv)
    source = Path(args.session)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    session = load_session(source)
    if session["session_id"] != "6255d38d-6757-42b8-890d-c600016148e8":
        parser.error("Este contraste fija las tres discrepancias de la sesión 6255d38d.")
    block, metadata = load_few_shot()
    if any(session["interventions"][n-1]["text"] in block for n in TARGETS):
        parser.error("Una pregunta de contraste aparece en las demostraciones.")
    output = Path(__file__).resolve().parents[1] / "outputs/results" / ("classifier-few-shot-ab-" + str(uuid4()) + ".json")
    report = {"experiment_version": "1.0.0", "scope": "three_known_development_discrepancies_not_blind_validation",
        "source_session_id": session["session_id"], "source_sha256": before,
        "model": args.model, "provider": "ollama", "few_shot_selection": metadata,
        "targets": TARGETS, "state": "running", "cases": [], "not_executed": [[mode,n] for n in TARGETS for mode in ("baseline", "few_shot")],
        "limits": {"max_output_tokens": 2048, "generations_per_case": 2, "planned_comparisons": 6}}
    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        env = {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model}
        with create_classification_client(env) as client:
            report["temperature"] = client.settings.temperature
            classifiers = {"baseline": LLMQuestionClassifier(client, few_shot=False), "few_shot": LLMQuestionClassifier(client, few_shot=True)}
            for number, expected in TARGETS.items():
                event = session["interventions"][number-1]
                context = select_classification_context(session["attempts"][:event["before_question_number"]-1])
                for mode, classifier in classifiers.items():
                    trace = classifier.classify(event["text"], intervention_id=event["intervention_id"],
                        configuration=session["configuration"], context_turns=context).to_dict()
                    decision = decide_response(trace["result"], expected_intervention_id=event["intervention_id"],
                        expected_text=event["text"], allowed_context_turn_ids=tuple(c["turn_number"] for c in context))
                    comparison = compare_prediction(trace["result"], expected)
                    report["cases"].append({"mode": mode, "intervention_number": number, "text": event["text"],
                        "context_turn_ids": [c["turn_number"] for c in context], "expected": expected,
                        "response_policy": decision.to_dict(), "trace": trace, **comparison})
                    report["not_executed"].remove([mode, number])
                    save()
                    print(json.dumps({"mode": mode, "intervention": number, "action": decision.action,
                        "semantic_match": comparison["semantic_match"], "differences": comparison["differences"],
                        "attempts": len(trace["attempts"])}, ensure_ascii=False), flush=True)
                    if trace["result"]["technical_error"] is not None:
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
        report["source_unchanged"] = before == hashlib.sha256(source.read_bytes()).hexdigest()
        report["summary"] = {mode: {"executed": sum(c["mode"]==mode for c in report["cases"]),
            "semantic_matches": sum(c["mode"]==mode and c["semantic_match"] for c in report["cases"])} for mode in ("baseline","few_shot")}
        save()
    print("Informe:", output, flush=True)
    return 0 if report["state"]=="completed" and report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

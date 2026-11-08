"""Revisar hasta cuatro bloqueos originales, sin candidato ni evaluador."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.intervention_log import select_classification_context
from harness.llm_question_classifier import ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client
from harness.session_log import load_session
from harness.response_policy import decide_response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--intervention", type=int, action="append", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args(argv)
    if not 1 <= len(args.intervention) <= 4 or len(set(args.intervention)) != len(args.intervention):
        parser.error("Selecciona hasta cuatro intervenciones diferentes.")
    source = Path(args.session)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    session = load_session(source)
    events = session.get("interventions", [])
    if any(not 1 <= n <= len(events) or events[n-1]["policy"]["action"] != "error_tecnico" for n in args.intervention):
        parser.error("Las intervenciones seleccionadas deben corresponder a bloqueos técnicos registrados.")
    if len({events[n-1]["text"] for n in args.intervention}) != len(args.intervention):
        parser.error("No repitas una misma pregunta para buscar un resultado favorable.")
    output = Path(__file__).resolve().parents[1] / "outputs/results" / ("classifier-blocks-probe-" + str(uuid4()) + ".json")
    report = {"probe_version": "1.0.0", "source_session_id": session["session_id"], "source_sha256": source_hash,
              "scope": "classifier_only_original_context", "semantic_review": "pending_human_review",
              "provider": "ollama", "model": args.model, "state": "running", "cases": [],
              "not_executed": list(args.intervention)}
    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        env = {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model}
        with create_classification_client(env, settings=ClassificationLLMSettings(args.model, 2048)) as client:
            classifier = HybridQuestionClassifier(LLMQuestionClassifier(client))
            for number in args.intervention:
                event = events[number-1]
                context = select_classification_context(session["attempts"][:event["before_question_number"] - 1])
                result = classifier.classify(event["text"], intervention_id=event["intervention_id"],
                                              configuration=session["configuration"], context_turns=context).to_dict()
                decision = decide_response(result["result"], expected_intervention_id=event["intervention_id"],
                    expected_text=event["text"], allowed_context_turn_ids=tuple(c["turn_number"] for c in context))
                report["cases"].append({"intervention_number": number, "text": event["text"],
                    "context_turn_ids": [c["turn_number"] for c in context], "report": result,
                    "response_policy": decision.to_dict()})
                report["not_executed"].remove(number)
                save()
                trace = result["trace"]["llm"]
                print(json.dumps({"intervention": number, "status": result["status"], "route": result["route"],
                    "units": len(result["result"]["units"]), "attempts": 0 if trace is None else len(trace["attempts"]),
                    "action": decision.action, "error": result["result"]["technical_error"]}, ensure_ascii=False), flush=True)
                if decision.action != "responder":
                    report["state"] = "stopped_on_block"
                    break
        if report["state"] == "running":
            report["state"] = "completed"
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except Exception:
        report["state"] = "error"
    finally:
        report["source_unchanged"] = source_hash == hashlib.sha256(source.read_bytes()).hexdigest()
        save()
    print("Informe:", output, flush=True)
    return 0 if report["state"] == "completed" and report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

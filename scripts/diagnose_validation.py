"""Repetir una sola intervención de una sesión con auditoría segura y Ollama."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.intervention_log import select_classification_context
from harness.llm_question_classifier import (
    ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)
from harness.session_log import load_session


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--intervention", type=int, required=True)
    args = parser.parse_args(argv)
    session = load_session(args.session)
    if not 1 <= args.intervention <= len(session.get("interventions", [])):
        parser.error("La intervención no existe en esta sesión.")
    event = session["interventions"][args.intervention - 1]
    context = select_classification_context(session["attempts"][:event["before_question_number"] - 1])
    source_hash = hashlib.sha256(args.session.read_bytes()).hexdigest()
    path = ROOT / "outputs/results" / f"validation-audit-{uuid4()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    print("Diagnóstico de una intervención; máximo una reparación. Sin salida cruda ni candidato.", flush=True)
    with create_classification_client(
        {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": "gemma4:e4b"},
        settings=ClassificationLLMSettings("gemma4:e4b", 2048),
    ) as client:
        observed = HybridQuestionClassifier(LLMQuestionClassifier(client)).classify(
            event["text"], intervention_id=event["intervention_id"],
            configuration=session["configuration"], context_turns=context,
        ).to_dict()
    llm = observed["trace"]["llm"]
    report = {
        "audit_version": "1.0.0", "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": session["session_id"], "intervention_number": args.intervention,
        "source_sha256": source_hash,
        "source_unchanged": source_hash == hashlib.sha256(args.session.read_bytes()).hexdigest(),
        "context_turn_ids": [turn["turn_number"] for turn in context],
        "provider": "ollama", "model": "gemma4:e4b", "max_output_tokens": 2048,
        "route": observed["route"], "status": observed["status"],
        "classifier_version": None if llm is None else llm["classifier_version"],
        "llm_contract_version": None if llm is None else llm["llm_contract_version"],
        "aggregation_version": None if llm is None else llm["aggregation_version"],
        "aggregation_applied": False if llm is None else llm["aggregation_applied"],
        "prompt_sha256": None if llm is None else llm["prompt_sha256"],
        "technical_error": observed["result"]["technical_error"],
        "attempts": [] if llm is None else llm["attempts"], "raw_logging": False,
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print(f"Informe: {path}", flush=True)
    return 0 if report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

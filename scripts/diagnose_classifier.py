"""Diagnóstico local explícito de tres casos, con contenido crudo y validación."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import argparse

import httpx

from harness.classification_contract import (
    ClassificationContractError,
)
from harness.llm_classification_contract import LLM_CONTRACT_VERSION, complete_llm_classification
from harness.classification_evaluation import assess_case, grouped_metrics
from harness.classification_references import load_classification_references
from harness.hybrid_question_classifier import HybridQuestionClassifier
from harness.json_loader import JsonTextError, parse_json_text
from harness.llm_question_classifier import (
    ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)
from harness.question_classifier import classify_local


ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = ("R04", "R08", "R26")
SOURCES = ("agent/classifier.md", "harness/llm/ollama_client.py", "harness/llm/factory.py",
           "harness/llm_question_classifier.py", "harness/classification_contract.py", "harness/classification_aggregation.py",
           "harness/llm_classification_contract.py", "schemas/llm_question_classification.schema.json",
           "harness/question_classifier.py", "schemas/question_classification.schema.json",
           "data/reference_questions/clasificacion_basica.json", "data/candidates/candidato_junior.json",
           "data/jobs/desarrollador_junior.json", "config/interviews/basica.json", "agent/agent.md")


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES}


def diagnose_text(text, request):
    """Analizar sin corregir, quitar Markdown o utilizar expectativas humanas."""
    try:
        draft = parse_json_text(text)
    except JsonTextError:
        detail = {"status": "json_invalido", "path": None, "rule": "strict_json"}
        try:
            json.loads(text)
        except json.JSONDecodeError as error:
            detail.update(line=error.lineno, column=error.colno, position=error.pos)
        except (ValueError, RecursionError):
            pass
        return detail
    try:
        complete_llm_classification(draft, expected_intervention_id=request["intervention_id"],
            expected_text=request["text"], allowed_context_turn_ids=tuple(t["turn_number"] for t in request["context_turns"]))
    except ClassificationContractError as error:
        return {"status": "contrato_invalido", "path": error.path, "rule": error.rule}
    return {"status": "validada", "path": None, "rule": None}


class RecordingTransport(httpx.BaseTransport):
    """Registrar solo message.content; sin cabeceras, solicitud o thinking."""

    def __init__(self, directory, requests, delegate=None):
        self.directory = directory
        self.requests = requests
        self.delegate = httpx.HTTPTransport() if delegate is None else delegate
        self.records = []

    def close(self):
        self.delegate.close()

    def handle_request(self, request):
        if (request.url.scheme != "http" or request.url.host != "127.0.0.1" or
                request.url.port != 11434 or request.url.path != "/api/chat" or
                request.method != "POST" or "authorization" in request.headers):
            raise ValueError("El diagnóstico solo permite Ollama local sin credenciales.")
        payload = json.loads(request.content)
        source = json.loads(payload["messages"][-1]["content"])["input"]
        identifier = source["intervention_id"]
        if identifier not in CASE_IDS or source != self.requests[identifier]:
            raise ValueError("Entrada fuera de los tres casos de desarrollo autorizados.")
        number = 1 + sum(r["case_id"] == identifier for r in self.records)
        if number > 2:
            raise ValueError("El diagnóstico no permite una tercera generación por caso.")
        response = self.delegate.handle_request(request)
        response.read()
        record = {"case_id": identifier, "attempt": number, "http_status": response.status_code,
                  "raw_output_file": None, "diagnosis": None,
                  "format_schema_sha256": hashlib.sha256(json.dumps(payload["format"], sort_keys=True,
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest() if "format" in payload else None}
        try:
            body = response.json()
        except (ValueError, RecursionError):
            body = None
        content = body.get("message", {}).get("content") if isinstance(body, dict) and isinstance(body.get("message"), dict) else None
        if 200 <= response.status_code < 300 and isinstance(content, str):
            raw_name = f"{identifier}-attempt-{number}.txt"
            raw = content.encode("utf-8")
            with (self.directory / raw_name).open("xb") as target:
                target.write(raw)
            record.update(raw_output_file=raw_name, raw_output_sha256=hashlib.sha256(raw).hexdigest(),
                          raw_output_bytes=len(raw), diagnosis=diagnose_text(content, source))
        with (self.directory / f"{identifier}-attempt-{number}.json").open("x", encoding="utf-8") as target:
            json.dump(record, target, ensure_ascii=False, indent=2, allow_nan=False)
            target.write("\n")
        self.records.append(record)
        return response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemma4:e4b")
    parser.add_argument("--format", choices=("prompt", "schema"), default="schema")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/results")
    args = parser.parse_args(argv)
    suite = load_classification_references()
    selected = {c["case_id"]: c for c in suite.cases() if c["case_id"] in CASE_IDS}
    requests = {i: suite.input_for(i) for i in CASE_IDS}
    if len(selected) != 3 or any(classify_local(**request).status != "abstencion" for request in requests.values()):
        raise ValueError("Se requieren tres abstenciones de desarrollo sin etiquetas en la entrada.")
    directory = args.output_dir / f"classifier-diagnostic-{args.format}-{uuid4()}"
    directory.mkdir(parents=True, exist_ok=False)
    transport = RecordingTransport(directory, requests)
    report = {"diagnostic_version": "1.1.0", "llm_contract_version": LLM_CONTRACT_VERSION,
              "stage": args.format, "created_at": datetime.now(timezone.utc).isoformat(),
              "state": "running", "case_ids": list(CASE_IDS), "provider": "ollama", "model": args.model,
              "max_output_tokens": 2048, "raw_logging": "explicit_three_development_cases_only",
              "source_hashes_before": hashes(), "cases": [], "attempts": transport.records}
    path = directory / "report.json"

    def save():
        with path.open("w", encoding="utf-8") as target:
            json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
            target.write("\n")

    code = 1
    try:
        save()
        with create_classification_client(
                {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": args.model},
                settings=ClassificationLLMSettings(args.model, 2048), structured_output=args.format == "schema",
                transport=transport) as client:
            classifier = HybridQuestionClassifier(LLMQuestionClassifier(client))
            print(f"Diagnóstico {args.format}, solo {', '.join(CASE_IDS)}. Informe: {path}", flush=True)
            for identifier in CASE_IDS:
                if hashes() != report["source_hashes_before"]:
                    raise ValueError("Una fuente cambió durante el diagnóstico.")
                print(f"  {identifier}: clasificando y registrando contenido crudo...", flush=True)
                observed = classifier.classify(**requests[identifier]).to_dict()
                entry = assess_case(selected[identifier], requests[identifier], observed)
                report["cases"].append(entry)
                save()
                print(f"  {identifier}: {entry['outcome']}; coincide={entry['exact_semantic_match']}", flush=True)
        report["state"] = "completed"
        code = 0
    except KeyboardInterrupt:
        report["state"] = "interrupted"
    except (ValueError, OSError):
        report["state"] = "error"
        print("Diagnóstico detenido; se conservan los registros disponibles.", flush=True)
    finally:
        transport.close()
        report.update(finished_at=datetime.now(timezone.utc).isoformat(), source_hashes_after=hashes(),
                      metrics=grouped_metrics(report["cases"]))
        report["sources_unchanged"] = report["source_hashes_before"] == report["source_hashes_after"]
        if not report["sources_unchanged"]:
            code = 1
            report["state"] = "error"
        save()
        print(f"Guardado: {path}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

"""Evaluar referencias de clasificación: reglas sin red o híbrido en Ollama local."""

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from harness.classification_evaluation import EVALUATION_VERSION, assess_case, grouped_metrics
from harness.classification_aggregation import AGGREGATION_VERSION
from harness.llm_classification_contract import LLM_CONTRACT_VERSION
from harness.classification_references import DEFAULT_REFERENCES_PATH, load_classification_references
from harness.hybrid_question_classifier import HYBRID_CLASSIFIER_VERSION, HybridQuestionClassifier
from harness.json_loader import load_json
from harness.llm_question_classifier import (
    CLASSIFIER_VERSION, ClassificationLLMSettings, LLMQuestionClassifier, create_classification_client,
)
from harness.question_classifier import LOCAL_CLASSIFIER_VERSION, classify_local


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "outputs/results"
FROZEN_SOURCES = ["agent/classifier.md", "schemas/question_classification.schema.json",
    "config/classifier_few_shot.json", "harness/classifier_few_shot.py",
    "schemas/llm_question_classification.schema.json", "harness/llm_classification_contract.py",
    "harness/classification_contract.py", "harness/classification_aggregation.py", "harness/classification_input.py", "harness/question_classifier.py",
    "harness/llm_question_classifier.py", "harness/hybrid_question_classifier.py", "harness/llm/factory.py",
    "harness/llm/ollama_client.py", "harness/llm/config.py", "harness/classification_evaluation.py",
    "scripts/evaluate_classifier.py", "data/candidates/candidato_junior.json", "agent/agent.md",
    "data/jobs/desarrollador_junior.json", "config/interviews/basica.json",
    "data/reference_questions/clasificacion_basica.json"]


def source_hashes():
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in FROZEN_SOURCES}


def _save(path, report):
    """Reemplazar solo el archivo de esta ejecución, después de escribirlo completo."""
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as target:
            temp = Path(target.name)
            json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
            target.write("\n")
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def _utc():
    return datetime.now(timezone.utc).isoformat()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("reglas", "hibrido"))
    parser.add_argument("--split", choices=("desarrollo", "comprobacion_conocida", "todos"))
    parser.add_argument("--case-id", action="append", help="Limitar a estos casos del grupo; repetible.")
    parser.add_argument("--suite", type=Path, default=DEFAULT_REFERENCES_PATH)
    parser.add_argument("--model")
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args(argv)
    report, output, writable = None, None, False
    try:
        saved = None if args.resume is None else load_json(args.resume)
        if saved is not None and (saved.get("evaluation_version") != EVALUATION_VERSION or args.output_dir is not None):
            raise ValueError("La reanudación requiere informe compatible y su directorio original.")
        old = {} if saved is None else saved["execution"]
        mode = args.mode or old.get("mode", "reglas")
        split = args.split or old.get("split", "desarrollo")
        model = args.model or old.get("model") or "gemma4:e4b"
        budget = args.max_output_tokens if args.max_output_tokens is not None else old.get("max_output_tokens", 2048)
        settings = ClassificationLLMSettings(model, budget)
        suite = load_classification_references(args.suite)
        data = suite.to_dict()
        cases = [c for c in data["cases"] if split == "todos" or c["split"] == split]
        selected = args.case_id if args.case_id is not None else old.get("case_ids")
        if selected is not None:
            if not selected or len(set(selected)) != len(selected) or not set(selected) <= {c["case_id"] for c in cases}:
                raise ValueError("Los casos deben ser únicos y pertenecer al grupo solicitado.")
            cases = [c for c in cases if c["case_id"] in selected]
        fingerprints = source_hashes()
        dataset = {"suite_id": data["suite_id"], "suite_version": data["suite_version"],
                   "source_sha256": suite.source_sha256, "contract_version": data["classification_contract_version"],
                   "cases_sha256": hashlib.sha256(json.dumps(data["cases"], ensure_ascii=False,
                       sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()}
        execution = {"mode": mode, "split": split, "provider": "ollama" if mode == "hibrido" else None,
                     "model": model if mode == "hibrido" else None, "max_output_tokens": budget,
                     "classification_only": True, "external_api": False,
                     "case_ids": None if selected is None else [c["case_id"] for c in cases]}
        if saved is not None:
            if (saved["execution"] != execution or saved["dataset"] != dataset
                    or saved["source_hashes_before"] != fingerprints
                    or saved["selected_case_ids"] != [c["case_id"] for c in cases]
                    or [e["case_id"] for e in saved["cases"]] != [c["case_id"] for c in cases[:len(saved["cases"])]]):
                raise ValueError("La configuración, fuentes o secuencia no coincide; no se repetirán casos.")
            # Recalcular desde la observación, sin confiar en métricas o etiquetas derivadas guardadas.
            rebuilt = []
            for case, entry in zip(cases, saved["cases"]):
                if entry["observation"] is None:
                    raise ValueError("Una observación inválida no admite reanudación automática.")
                request = suite.input_for(case["case_id"], split=case["split"])
                if entry["input"] != request:
                    raise ValueError("La entrada guardada no coincide con su fuente.")
                rebuilt.append(assess_case(case, request, entry["observation"]))
            report = saved
            report["cases"] = rebuilt
            output = args.resume.resolve()
            writable = True
        else:
            directory = RESULTS_DIR if args.output_dir is None else args.output_dir
            directory.mkdir(parents=True, exist_ok=True)
            identifier = str(uuid4())
            output = directory / f"classification-evaluation-{mode}-{identifier}.json"
            report = {"evaluation_version": EVALUATION_VERSION, "run_id": identifier, "created_at": _utc(),
                "finished_at": None, "state": "running", "semantic_review": "pending_human_review",
                "dataset": dataset, "execution": execution, "selected_case_ids": [c["case_id"] for c in cases],
                "source_hashes_before": fingerprints, "source_hashes_after": None, "sources_unchanged": None,
                "versions": {"local": LOCAL_CLASSIFIER_VERSION, "llm": CLASSIFIER_VERSION,
                             "llm_contract": LLM_CONTRACT_VERSION, "aggregation": AGGREGATION_VERSION,
                             "hybrid": HYBRID_CLASSIFIER_VERSION},
                "cases": [], "metrics": None, "issues": []}
            with output.open("x", encoding="utf-8") as target:
                json.dump(report, target, ensure_ascii=False, indent=2, allow_nan=False)
            writable = True
        report.update(state="running", finished_at=None, metrics=grouped_metrics(report["cases"]))
        _save(output, report)
        print(f"Evaluación {mode}: {len(cases)} casos; {len(report['cases'])} ya registrados. Informe: {output}", flush=True)
        with ExitStack() as stack:
            classifier = None
            if mode == "hibrido" and len(report["cases"]) < len(cases):
                # Entorno explícito: no clave, archivo privado, selección externa o cambio de presupuesto.
                client = stack.enter_context(create_classification_client(
                    {"LLM_PROVIDER": "ollama", "LLM_ALLOW_EXTERNAL_API": "false", "OLLAMA_MODEL": model}, settings=settings))
                classifier = HybridQuestionClassifier(LLMQuestionClassifier(client))
            for case in cases[len(report["cases"]):]:
                if (source_hashes() != fingerprints or
                        hashlib.sha256(suite.source_path.read_bytes()).hexdigest().upper() != suite.source_sha256):
                    raise ValueError("Una fuente cambió durante la ejecución; se detuvo sin ajustar resultados.")
                request = suite.input_for(case["case_id"], split=case["split"])
                print(f"  {case['case_id']} ({case['split']}): clasificando...", flush=True)
                observed = (classify_local(**request) if mode == "reglas" else classifier.classify(**request)).to_dict()
                report["cases"].append(assess_case(case, request, observed))
                report["metrics"] = grouped_metrics(report["cases"])
                _save(output, report)
                latest = report["cases"][-1]
                print(f"  {case['case_id']}: {latest['outcome']}; coincidencia descriptiva={latest['exact_semantic_match']}", flush=True)
        report["state"] = "completed"
        code = 0
    except KeyboardInterrupt:
        code = 1
        if report is not None:
            report["state"] = "interrupted"
            report["issues"].append("interrupted")
        print("Evaluación interrumpida; se conservan los casos terminados.", flush=True)
    except (ValueError, OSError, KeyError, TypeError):
        code = 1
        if report is not None:
            report["state"] = "error"
            report["issues"].append("evaluation_error")
        print("No se completó la evaluación; revisa fuentes, parámetros y archivo de resultados.", flush=True)
    finally:
        if report is not None and output is not None and writable:
            try:
                report["finished_at"] = _utc()
                report["source_hashes_after"] = source_hashes()
                report["sources_unchanged"] = (report["source_hashes_before"] == report["source_hashes_after"] and
                    hashlib.sha256(suite.source_path.read_bytes()).hexdigest().upper() == suite.source_sha256)
                if not report["sources_unchanged"]:
                    report["state"] = "error"
                    code = 1
                report["metrics"] = grouped_metrics(report["cases"])
                _save(output, report)
                print(f"Guardado: {output}", flush=True)
            except (OSError, ValueError):
                code = 1
                print("No se confirmó el guardado final; los puntos de control previos pueden conservarse.", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

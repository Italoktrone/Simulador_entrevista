"""Seis demostraciones aprobadas, sin datos del candidato ni casos reservados."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path

from harness.evaluation_contract import DEMONSTRATION_CASES, complete_evaluation, evaluation_request_schema
from harness.json_loader import parse_json_text
from harness.quality_references import REFERENCE_PATH, load_quality_references
from harness.schema_validator import validate_data
from harness.scoring import CRITERIA, load_rubric, validate_rubric

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/evaluator_few_shot.json"
DEMONSTRATIONS_PATH = ROOT / "data/reference_questions/evaluator_demonstrations.json"
JOB_PATH = ROOT / "data/jobs/desarrollador_junior.json"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)


def disabled_few_shot(reason="disabled_by_option"):
    return {"enabled": False, "version": "1.0.0", "case_ids": [], "reference_sha256": None,
            "examples_sha256": None, "job_sha256": None, "reason": reason}


@lru_cache(maxsize=8)
def _compile(config_raw, references_raw, demonstrations_raw, job_raw, rubric_json):
    config = parse_json_text(config_raw.decode("utf-8"))
    required = {"few_shot_version", "rubric_version", "reference_sha256", "demonstrations_sha256", "job_sha256", "case_ids", "rubric_definition_sha256"}
    if (not isinstance(config, dict) or set(config) != required or config["few_shot_version"] != "1.0.0"
            or config["case_ids"] != list(DEMONSTRATION_CASES)):
        raise ValueError("Selección de demostraciones del evaluador incompatible.")
    for key, raw in (("reference_sha256", references_raw), ("demonstrations_sha256", demonstrations_raw), ("job_sha256", job_raw)):
        if config[key] != hashlib.sha256(raw).hexdigest():
            raise ValueError("Cambió una fuente de las demostraciones aprobadas.")
    references, demos, job = (parse_json_text(raw.decode("utf-8")) for raw in (references_raw, demonstrations_raw, job_raw))
    rubric = validate_rubric(parse_json_text(rubric_json))
    definition = canonical({k: rubric[k] for k in ("rubric_version", "descriptors")})
    if hashlib.sha256(definition.encode()).hexdigest() != config["rubric_definition_sha256"]:
        raise ValueError("La definición de rúbrica no coincide con las demostraciones aprobadas.")
    if references["rubric_version"] != config["rubric_version"] or config["rubric_version"] != rubric["rubric_version"]:
        raise ValueError("Las demostraciones requieren su rúbrica aprobada.")
    if (not isinstance(demos, dict) or set(demos) != {"demonstrations_version", "examples"}
            or demos["demonstrations_version"] != "1.0.0"
            or [e["case_id"] for e in demos["examples"]] != config["case_ids"]):
        raise ValueError("Demostraciones incompatibles con la selección aprobada.")
    by_id = {c["case_id"]: c for c in references["cases"]}
    examples = []
    for demo in demos["examples"]:
        case = by_id[demo["case_id"]]
        if case["review_status"] != "approved" or not case["reviewer"] or case["split"] != "desarrollo":
            raise ValueError("Solo se inyectan demostraciones de desarrollo revisadas y aprobadas.")
        request = {"question": case["question"], "configuration": {"approach": case["approach"]}, "job": job,
                   "objective": case["objective"], "competency": case["competency"],
                   "context_turns": case["context_turns"], "classification": case["classification"]}
        validate_data(request, evaluation_request_schema())
        analysis = complete_evaluation(demo["output"], request)
        if ({k: analysis["criteria"][k]["level"] for k in CRITERIA} != case["expected"]["levels"]
                or {k: analysis["criteria"][k]["reason"] for k in CRITERIA} != case["expected"]["justifications"]):
            raise ValueError("La demostración no reproduce los niveles y razones aprobados.")
        compact_input = {k: v for k, v in request.items() if k not in {"job", "configuration"}}
        compact_input["interview_approach"] = case["approach"]
        examples.append({"input": compact_input, "output": demo["output"]})
    encoded = json.dumps(examples, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    block = ("\nDEMOSTRACIONES APROBADAS DE DESARROLLO:\n"
             "Son ejemplos independientes para el mismo cargo del input real. Las entradas abreviadas heredan ese cargo; "
             "interview_approach es su enfoque de entrevista. Cada input tiene su propio objective y contexto; "
             "no transfieras hechos, objetivos o antecedentes de un ejemplo al caso actual. "
             "Imita el criterio de evaluación y el formato, usando solo la evidencia del input actual.\n" + encoded)
    metadata = {"enabled": True, "version": config["few_shot_version"], "case_ids": config["case_ids"],
                "reference_sha256": config["reference_sha256"], "examples_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "job_sha256": config["job_sha256"], "reason": "active"}
    return block, json.dumps(metadata), canonical(job)


def load_evaluator_examples(rubric, config_path=CONFIG_PATH, references_path=REFERENCE_PATH,
                            demonstrations_path=DEMONSTRATIONS_PATH, job_path=JOB_PATH):
    # El cargador general valida los 40 globales con la regla vigente. La caché
    # usa los contenidos completos; cambiar un archivo invalida su compilación.
    raw = [Path(p).read_bytes() for p in (config_path, references_path, demonstrations_path, job_path)]
    key = (*raw, canonical(validate_rubric(rubric)))
    load_quality_references(references_path, rubric=load_rubric())
    block, metadata, job = _compile(*key)
    return block, json.loads(metadata), job

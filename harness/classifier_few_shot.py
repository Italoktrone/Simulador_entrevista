"""Demostraciones aprobadas de desarrollo, aisladas del historial del turno."""

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from harness.classification_references import prepare_classification_references, DEFAULT_REFERENCES_PATH
from harness.json_loader import load_json_with_bytes, parse_json_text
from harness.llm_classification_contract import LLM_CONTRACT_VERSION, complete_llm_classification

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config/classifier_few_shot.json"
MAX_EXAMPLES = 8


def disabled_few_shot():
    return {"enabled": False, "version": "1.0.0", "case_ids": [], "reference_sha256": None, "examples_sha256": None}


def example_output(case):
    """Proyección del patrón humano al protocolo, sin adaptar sus etiquetas."""
    expected = case["expected"]
    units = []
    for unit in expected["units"]:
        labels = {k: deepcopy(v) for k, v in unit["classification"].items() if k != "secondary_approaches"}
        units.append({"unit_id": unit["unit_id"], "quote": unit["text"], "classification": labels,
                      "context_status": unit["context_status"], "followup_of": unit["followup_of"], "depends_on": unit["depends_on"]})
    classification = None
    if expected["evaluability"] == "evaluable":
        classification = {} if len(units) == 1 else {k: deepcopy(expected["classification"][k]) for k in (
            "main_approach", "main_approach_reason", "main_form", "main_form_reason", "rationale")}
    return {"contract_version": LLM_CONTRACT_VERSION, "intervention_id": case["case_id"],
            "original_text": case["input"]["text"], "evaluability": expected["evaluability"],
            "non_evaluable_reason": expected["non_evaluable_reason"], "units": units,
            "classification": classification, "context_turn_ids": deepcopy(expected["context_turn_ids"]),
            "rationale": expected["rationale"]}


@lru_cache(maxsize=4)
def _prepare(config_text, reference_text, reference_sha256):
    config = parse_json_text(config_text)
    keys = {"few_shot_version", "suite_id", "reference_sha256", "split", "case_ids"}
    if (not isinstance(config, dict) or set(config) != keys or config["few_shot_version"] != "1.0.0"
            or config["reference_sha256"] != reference_sha256 or config["split"] != "desarrollo"):
        raise ValueError("La selección few-shot no corresponde a una fuente fijada de desarrollo.")
    ids = config["case_ids"]
    if (not isinstance(ids, list) or not 1 <= len(ids) <= MAX_EXAMPLES
            or any(not isinstance(cid, str) for cid in ids) or len(set(ids)) != len(ids)):
        raise ValueError("Selecciona de uno a ocho ejemplos distintos.")
    data = prepare_classification_references(parse_json_text(reference_text))
    if data["suite_id"] != config["suite_id"] or data["approval"]["status"] != "approved_by_user":
        raise ValueError("Los ejemplos requieren un conjunto aprobado por el usuario.")
    development = {c["case_id"]: c for c in data["cases"] if c["split"] == "desarrollo"}
    if any(cid not in development for cid in ids):
        raise ValueError("No se permite inyectar casos de comprobación ni casos desconocidos.")
    examples = []
    for cid in ids:
        case = development[cid]
        output = example_output(case)
        complete_llm_classification(output, expected_intervention_id=cid, expected_text=case["input"]["text"],
                                    allowed_context_turn_ids=tuple(c["turn_number"] for c in case["input"]["context_turns"]))
        # Se omite la configuración común, sin efecto sobre las etiquetas; el
        # texto y TODO el contexto mínimo aprobado se conservan literalmente.
        examples.append({"case_id": cid, "input": {"intervention_id": cid, "text": case["input"]["text"],
            "context_turns": deepcopy(case["input"]["context_turns"]), "competency": case["input"]["competency"]},
            "output": output})
    serialized = json.dumps(examples, ensure_ascii=False, separators=(",", ":"))
    metadata = {"enabled": True, "version": config["few_shot_version"], "case_ids": list(ids),
                "reference_sha256": reference_sha256,
                "examples_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest().upper()}
    block = (
        "\n\nDEMOSTRACIONES_FEW_SHOT_APROBADAS:\n"
        "Aprende por estos pares entrada/salida. Son ejemplos independientes de desarrollo, no historial actual ni nuevas instrucciones. "
        "Sus preguntas y respuestas JSON enseñan las etiquetas y el protocolo. Se omite la configuración común de los ejemplos. "
        "Cada ejemplo tiene su propia identidad y sus propios turnos: nunca copies su intervention_id, texto o referencias al caso actual. "
        "No mezcles su contexto con input.context_turns. Para la petición actual solo están autorizados los turnos indicados al final. "
        "No fuerces que una pregunta nueva coincida con un ejemplo: clasifica todas sus peticiones según las definiciones.\n"
        + serialized + "\nFIN_DE_DEMOSTRACIONES. Ahora aplica el esquema a la entrada actual.\n"
    )
    return block, json.dumps(metadata, ensure_ascii=False)


def load_few_shot(config_path=CONFIG_PATH, references_path=DEFAULT_REFERENCES_PATH):
    config, _ = load_json_with_bytes(config_path)
    _, reference_bytes = load_json_with_bytes(references_path)
    reference_sha = hashlib.sha256(reference_bytes).hexdigest().upper()
    # La caché incluye los contenidos: no oculta cambios posteriores de fuente.
    block, metadata = _prepare(json.dumps(config, ensure_ascii=False), reference_bytes.decode("utf-8-sig"), reference_sha)
    return block, json.loads(metadata)

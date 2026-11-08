"""Rúbrica provisional: cálculo exacto local, sin modelo ni imputaciones."""

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite
from pathlib import Path

from harness.json_loader import load_json

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/evaluation.json"
CRITERIA = ("pertinencia", "enfoque", "claridad", "neutralidad")
LEVELS = ("Inicial", "En desarrollo", "Logrado", "Destacado")


def validate_rubric(config: dict) -> dict:
    version = config.get("rubric_version") if isinstance(config, dict) else None
    expected = {"rubric_version", "weights", "thresholds",
                "context_pairs", "context_characters", "read_timeout_seconds", "max_output_tokens", "descriptors"}
    expected.add("block_distinguished_on_level_one" if version == "1.0.0" else "level_one_visible_cap")
    if version not in ("1.0.0", "1.1.0") or set(config) != expected:
        raise ValueError("Configuración de rúbrica incompatible.")
    def finite(value):
        return type(value) in (int, float) and isfinite(value)
    weights = config["weights"]
    if (not isinstance(weights, dict) or set(weights) != set(CRITERIA)
            or any(not finite(w) or w < 0 for w in weights.values())
            or abs(sum(Decimal(str(w)) for w in weights.values()) - 100) > Decimal("0.000001")):
        raise ValueError("Los cuatro pesos deben ser finitos, no negativos y sumar 100 (tolerancia 0,000001).")
    thresholds = config["thresholds"]
    if (not isinstance(thresholds, list) or len(thresholds) != 3
            or any(not finite(t) for t in thresholds)
            or not 1 < thresholds[0] < thresholds[1] < thresholds[2] < 4):
        raise ValueError("Se necesitan tres umbrales crecientes dentro de (1, 4).")
    if version == "1.0.0" and type(config["block_distinguished_on_level_one"]) is not bool:
        raise ValueError("La restricción de Destacado debe ser booleana.")
    if version == "1.1.0" and config["level_one_visible_cap"] != "En desarrollo":
        raise ValueError("La regla crítica 1.1.0 exige un máximo de En desarrollo ante cualquier nivel 1.")
    for key, minimum, maximum in (("context_pairs", 1, 10), ("context_characters", 100, 4000),
                                  ("max_output_tokens", 256, 4096)):
        if type(config[key]) is not int or not minimum <= config[key] <= maximum:
            raise ValueError("Límite de evaluación inválido: " + key)
    if not finite(config["read_timeout_seconds"]) or not 1 <= config["read_timeout_seconds"] <= 300:
        raise ValueError("La espera de lectura debe estar entre 1 y 300 segundos.")
    descriptors = config["descriptors"]
    if not isinstance(descriptors, dict) or set(descriptors) != set(CRITERIA):
        raise ValueError("Faltan descriptores de la rúbrica.")
    for values in descriptors.values():
        if (not isinstance(values, list) or len(values) != 4
                or any(not isinstance(v, str) or not v.strip() for v in values)):
            raise ValueError("Cada criterio requiere cuatro descriptores observables.")
    return deepcopy(config)


def load_rubric(path=CONFIG_PATH) -> dict:
    return validate_rubric(load_json(path))


def score_criteria(levels: dict, config: dict) -> dict:
    """Límites sobre promedio sin redondear; no se renormalizan faltantes."""
    config = validate_rubric(config)
    if not isinstance(levels, dict) or set(levels) != set(CRITERIA):
        raise ValueError("Se necesitan los cuatro criterios.")
    if any(v is not None and (type(v) is not int or not 1 <= v <= 4) for v in levels.values()):
        raise ValueError("Los niveles deben ser enteros entre 1 y 4, o null si falta evidencia.")
    empty = {"weighted_score": None, "normalized_score": None, "visible_level": None, "critical_cap_applied": False}
    if any(v is None for v in levels.values()):
        return empty
    # Normalizar los pesos aceptados dentro de la tolerancia declarada. Una suma
    # fuera de tolerancia siempre se rechaza; el archivo original se conserva.
    total = sum(Decimal(str(v)) for v in config["weights"].values())
    weighted = sum(Decimal(str(config["weights"][k])) * levels[k] for k in CRITERIA) / total
    if not Decimal(1) <= weighted <= Decimal(4):
        raise ValueError("Los pesos no producen un promedio dentro de la escala.")
    index = sum(weighted >= Decimal(str(t)) for t in config["thresholds"])
    maximum_index = 1 if config["rubric_version"] == "1.1.0" else 2
    enabled = config["rubric_version"] == "1.1.0" or config["block_distinguished_on_level_one"]
    cap = enabled and 1 in levels.values() and index > maximum_index
    if cap:
        index = maximum_index
    def rounded(value):
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"weighted_score": rounded(weighted), "normalized_score": rounded((weighted - 1) / 3 * 100),
            "visible_level": LEVELS[index], "critical_cap_applied": cap}

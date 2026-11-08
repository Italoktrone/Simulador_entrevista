"""Construcción explícita de fixtures del protocolo reducido, solo para pruebas."""
from copy import deepcopy

def to_wire(value):
    result = deepcopy(value)
    result["contract_version"] = "1.3.0"
    if result.get("classification") is not None:
        for key in ("approaches", "forms", "attributes", "certainty", "secondary_approaches"):
            result["classification"].pop(key, None)
    for unit in result["units"]:
        unit["classification"].pop("secondary_approaches", None)
    if result.get("evaluability") == "evaluable" and len(result["units"]) == 1:
        result["classification"] = {}
    elif result.get("evaluability") == "evaluable" and len(result["units"]) > 1:
        # Valores de construcción sintéticos, no reglas del clasificador.
        # Las referencias humanas ya contienen explícitamente estos campos.
        for key in ("main_approach", "main_approach_reason", "main_form", "main_form_reason", "rationale"):
            result["classification"].setdefault(key, result["units"][0]["classification"][key])
    return result

"""Derivados deterministas del protocolo LLM, sin decisiones de predominio."""

from copy import deepcopy

from harness.classification_contract import ClassificationContractError, _validate_labels, classification_expectation_schema


AGGREGATION_VERSION = "1.1.0"
GLOBAL_DERIVED_FIELDS = ("approaches", "forms", "attributes", "secondary_approaches", "certainty")


def build_derived_labels(document: dict) -> dict:
    """Recibe estructura LLM ya validada; nunca sustituye campos del modelo.

    El llamador rechaza los campos derivados en el protocolo de entrada.
    Las decisiones semánticas se conservan y se revalidan en el contrato público.
    """
    result = deepcopy(document)
    if result["evaluability"] != "evaluable":
        return result
    definitions = classification_expectation_schema()["$defs"]
    domains = {
        "approaches": definitions["approach"]["enum"],
        "forms": definitions["form"]["enum"],
        "attributes": definitions["classification"]["properties"]["attributes"]["items"]["enum"],
    }

    def ordered(values, field):
        return [label for label in domains[field] if label in values]

    def secondaries(labels):
        main = labels["main_approach"]
        return ordered(set(labels["approaches"]) - {main, "indeterminado"}, "approaches") if main is not None else []

    for index, unit in enumerate(result["units"]):
        labels = unit["classification"]
        for field in domains:
            labels[field] = ordered(labels[field], field)
        labels["secondary_approaches"] = secondaries(labels)
        _validate_labels(labels, f"/units/{index}/classification", unit=True)

    if len(result["units"]) == 1:
        # El protocolo 1.3 prohíbe al modelo repetir una decisión global que
        # por contrato debe coincidir con la de esta única unidad.
        if result["classification"]:
            raise ClassificationContractError("/classification", "single_unit_global",
                "La clasificación global de una sola unidad se deriva y no admite decisiones duplicadas.")
        labels = result["units"][0]["classification"]
        result["classification"] = {k: deepcopy(labels[k]) for k in (
            "main_approach", "main_approach_reason", "main_form", "main_form_reason", "rationale")}
    global_labels = result["classification"]
    for field, unknown in (("approaches", "indeterminado"), ("forms", "indeterminada"), ("attributes", None)):
        values = {v for unit in result["units"] for v in unit["classification"][field]}
        if unknown is not None and len(values) > 1:
            values.discard(unknown)
        global_labels[field] = ordered(values, field)
    global_labels["secondary_approaches"] = secondaries(global_labels)
    certainties = {unit["classification"]["certainty"] for unit in result["units"]}
    global_labels["certainty"] = ("clara" if certainties == {"clara"} else
                                  "indeterminada" if certainties == {"indeterminada"} else "ambigua")
    return result

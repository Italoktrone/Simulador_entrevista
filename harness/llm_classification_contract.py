"""Protocolo 1.3: no repetir decisiones globales de una unidad única."""

from copy import deepcopy
from itertools import combinations

from harness.classification_contract import (
    ClassificationContractError, classification_expectation_schema,
    validate_classification_expectation,
)
from harness.schema_validator import DataValidationError, validate_data
from harness.classification_aggregation import build_derived_labels, GLOBAL_DERIVED_FIELDS


LLM_CONTRACT_VERSION = "1.3.0"
MISSING_GLOBAL_APPROACH_REASON = "Justificación omitida por el motor de inferencia"


def _sets(values, *, empty=False, unknown=None, singleton=False):
    known = [value for value in values if value != unknown]
    result = [[]] if empty else []
    for size in range(1, 2 if singleton else len(known) + 1):
        result.extend(list(group) for group in combinations(known, size))
    if unknown is not None:
        result.append([unknown])
    return result


def classification_llm_schema():
    """Derivar el protocolo del modelo sin cambiar el contrato persistido."""
    schema = classification_expectation_schema()
    schema["title"] = "Respuesta del clasificador LLM con citas literales"
    schema["description"] = "Contrato LLM 1.3.0. Python deriva el global de una sola unidad y valida el resultado público 1.0.0."
    schema["properties"]["contract_version"] = {"const": LLM_CONTRACT_VERSION}
    labels = schema["$defs"]["classification"]["properties"]
    domains = schema["$defs"]
    for key, values, empty, unknown in (
        ("approaches", domains["approach"]["enum"], False, "indeterminado"),
        ("secondary_approaches", domains["known_approach"]["enum"], True, None),
        ("forms", domains["form"]["enum"], False, "indeterminada"),
        ("attributes", labels["attributes"]["items"]["enum"], True, None),
    ):
        labels[key].update(uniqueItems=True, maxItems=len(values))
    for key in ("main_approach_reason", "main_form_reason"):
        labels[key]["description"] = "Solo justificar prioridad entre varias etiquetas; con una etiqueta o sin principal debe ser null. La explicación general va en rationale."
    unit = schema["$defs"]["unit"]
    unit["required"] = [key for key in unit["required"] if key not in {"text", "source_start", "source_end"}]
    unit["required"].insert(1, "quote")
    for key in ("text", "source_start", "source_end"):
        unit["properties"].pop(key)
    props = unit["properties"]
    unit["properties"] = {"unit_id": props.pop("unit_id"),
        "quote": {"$ref": "#/$defs/text", "description": "Copia literal y contigua del texto original, sin reformular, corregir o calcular índices."}, **props}
    unit_labels = deepcopy(schema["$defs"]["classification"])
    unit_labels["properties"]["forms"].update(maxItems=1)
    unit_labels["properties"]["main_form_reason"] = {"type": "null"}
    schema["$defs"]["unit_classification"] = unit_labels
    unit["properties"]["classification"] = {"$ref": "#/$defs/unit_classification"}
    for definition, fields in ((schema["$defs"]["classification"], GLOBAL_DERIVED_FIELDS),
                               (unit_labels, ("secondary_approaches",))):
        for field in fields:
            definition["properties"].pop(field)
            definition["required"].remove(field)
    single = {"type": "object", "additionalProperties": False, "properties": {}}
    schema["$defs"]["single_global"] = single
    # Segmentar antes de emitir el global: así la generación decide si hay una
    # o varias unidades antes de comprometerse con un resumen que exige varias.
    keys = list(schema["properties"])
    keys.remove("units")
    keys.insert(keys.index("classification"), "units")
    schema["properties"] = {k: schema["properties"][k] for k in keys}
    required = schema["required"]
    required.remove("units")
    required.insert(required.index("classification"), "units")
    # Se sustituyen solo las condiciones del contenedor global del modelo.
    # El contrato público permanece intacto y se revalida tras expandirlo.
    schema["properties"]["classification"] = {"anyOf": [
        {"type": "null"}, {"$ref": "#/$defs/single_global"}, {"$ref": "#/$defs/classification"}]}
    schema.pop("allOf", None)
    schema["oneOf"] = [
        {"properties": {"evaluability": {"const": "no_evaluable"}, "classification": {"type": "null"}, "units": {"maxItems": 0}}},
        {"properties": {"evaluability": {"const": "evaluable"}, "non_evaluable_reason": {"type": "null"},
                        "classification": {"$ref": "#/$defs/single_global"}, "units": {"minItems": 1, "maxItems": 1}}},
        {"properties": {"evaluability": {"const": "evaluable"}, "non_evaluable_reason": {"type": "null"},
                        "classification": {"$ref": "#/$defs/classification"}, "units": {"minItems": 2}}},
    ]
    return schema


def _coherent_priority_schema(definition):
    """Alternativas de objetos completos: la gramática no depende de if/then."""
    branches = [definition]
    for plural, main, reason in (
        ("approaches", "main_approach", "main_approach_reason"),
        ("forms", "main_form", "main_form_reason"),
    ):
        expanded = []
        for branch in branches:
            choices = branch["properties"][plural]["enum"]
            if plural == "approaches":
                # Dominio finito: cada conjunto determina las opciones de
                # principal y razón, sin elegir una interpretación.
                for present in choices:
                    principals = present if len(present) == 1 else [None, *present]
                    for primary in principals:
                        alternative = deepcopy(branch)
                        props = alternative["properties"]
                        props[plural]["enum"] = [present]
                        props[main] = {"const":primary}
                        props[reason] = ({"$ref":"#/$defs/rationale"}
                                         if len(present) > 1 and primary is not None else {"type":"null"})
                        expanded.append(alternative)
                continue
            singles = [option for option in choices if len(option) == 1]
            multiple = [option for option in choices if len(option) > 1]
            for options, principal, justification in (
                (singles, {"enum": [option[0] for option in singles]}, {"type":"null"}),
                (multiple, {"type":"null"}, {"type":"null"}),
                (multiple, {"enum": sorted({v for option in multiple for v in option})}, {"$ref":"#/$defs/rationale"}),
            ):
                if not options:
                    continue
                alternative = deepcopy(branch)
                props = alternative["properties"]
                props[plural]["enum"] = options
                props[main] = principal
                props[reason] = justification
                expanded.append(alternative)
        branches = expanded
    return {"oneOf":branches}


def classification_generation_schema(*, allowed_context_turn_ids: tuple[int, ...] | None = None):
    """Restringir la generación nativa a conjuntos canónicos sin duplicados.

    Equivale a una presentación ordenada de los conjuntos permitidos, sin
    escoger etiquetas. El parser acepta cualquier permutación única válida.
    Evita depender solo del soporte de uniqueItems del motor de generación.
    Con turnos autorizados, cierra sus dominios para esta solicitud. None
    mantiene la plantilla genérica; () representa ausencia real de historial.
    """
    schema = classification_llm_schema()
    # Razones cortas para generación. El parser conserva el límite público y
    # no trunca silenciosamente salidas o anotaciones humanas.
    schema["$defs"]["rationale"]["maxLength"] = 160
    domains = schema["$defs"]
    for definition in ("unit_classification",):
        labels = domains[definition]["properties"]
        for key, values, empty, unknown in (
            ("approaches", domains["approach"]["enum"], False, "indeterminado"),
            ("forms", domains["form"]["enum"], False, "indeterminada"),
            ("attributes", labels["attributes"]["items"]["enum"], True, None),
        ):
            labels[key]["enum"] = _sets(values, empty=empty, unknown=unknown,
                singleton=definition == "unit_classification" and key == "forms")
    if allowed_context_turn_ids is not None:
        ids = allowed_context_turn_ids
        if (not isinstance(ids, tuple) or any(type(n) is not int or n < 1 for n in ids)
                or tuple(sorted(set(ids))) != ids):
            raise ValueError("Los turnos autorizados deben ser enteros positivos únicos y ordenados.")
        turns = domains["turn_ids"]
        turns["maxItems"] = len(ids)
        if ids:
            turns["items"]["enum"] = list(ids)
            # La ventana normal tiene dos turnos. También cerrar las listas
            # sin depender de uniqueItems en el motor de generación.
            if len(ids) <= 2:
                turns["enum"] = _sets(ids, empty=True)
        else:
            turns.update(const=[], enum=[[]])
        domains["unit"]["properties"]["followup_of"] = {"enum": [None, *ids]}
        for name in ("unit_classification",):
            domains[name] = _coherent_priority_schema(domains[name])
    # Alternativas completas para la gramática nativa: 0, 1 o varias unidades.
    # No requiere que el motor interprete if/then ni relaciones entre campos.
    constraints = schema.pop("oneOf")
    schema.pop("allOf", None)
    branches = []
    for constraint in constraints:
        branch = {k: deepcopy(v) for k, v in schema.items() if k not in {"$defs", "title", "description"}}
        for key, value in constraint["properties"].items():
            if key == "units":
                branch["properties"][key].update(value)
            else:
                branch["properties"][key] = deepcopy(value)
        branches.append(branch)
    schema = {"$defs": domains, "oneOf": branches}
    return schema


def locate_quotes(original, quotes):
    """Encontrar el único alineamiento ordenado y sin solapamientos.

    El alineamiento más temprano (find) y el más tardío (rfind) delimitan
    todos los válidos. Si difieren, no se elige arbitrariamente. Se conservan
    espacios, mayúsculas y Unicode sin normalización.
    """
    if not isinstance(original, str) or any(not isinstance(q, str) or not q.strip() for q in quotes):
        raise ClassificationContractError("/units", "quote_input", "Se requieren fragmentos literales no vacíos.")
    earliest, cursor = [], 0
    for index, quote in enumerate(quotes):
        start = original.find(quote, cursor)
        if start < 0:
            rule = "quote_not_found" if original.find(quote) < 0 else "quote_order"
            raise ClassificationContractError(f"/units/{index}/quote", rule,
                "Los fragmentos deben existir literalmente, estar ordenados y no solaparse.")
        end = start + len(quote)
        earliest.append((start, end))
        cursor = end
    latest = [None] * len(quotes)
    cursor = len(original)
    for index in range(len(quotes) - 1, -1, -1):
        start = original.rfind(quotes[index], 0, cursor)
        latest[index] = (start, start + len(quotes[index]))
        cursor = start
    if earliest != latest:
        raise ClassificationContractError("/units", "quote_ambiguous",
            "Los fragmentos admiten más de un alineamiento; no se puede elegir una posición inequívoca.")
    return earliest


def _complete_missing_global_approach_reason(data):
    """Completar solo la omisión global autorizada, antes del esquema estricto.

    El texto identifica una omisión del motor; no aporta evidencia semántica
    de predominio. No elige un principal ni modifica las unidades o formas.
    El validador público sigue comprobando todas las demás relaciones.
    """
    if not isinstance(data, dict):
        return data
    units, labels = data.get("units"), data.get("classification")
    if not isinstance(units, list) or len(units) < 2 or not isinstance(labels, dict):
        return data
    main, reason = labels.get("main_approach"), labels.get("main_approach_reason")
    if not isinstance(main, str) or not (reason is None or isinstance(reason, str) and reason == ""):
        return data
    present = set()
    for unit in units:
        if not isinstance(unit, dict) or not isinstance(unit.get("classification"), dict):
            return data
        approaches = unit["classification"].get("approaches")
        if not isinstance(approaches, list) or not approaches or any(not isinstance(v, str) for v in approaches):
            return data
        present.update(approaches)
    present.discard("indeterminado")
    if len(present) < 2 or main not in present:
        return data
    result = deepcopy(data)
    result["classification"]["main_approach_reason"] = MISSING_GLOBAL_APPROACH_REASON
    return result


def _normalize_global_main_form(data):
    """Anular una forma global ajena al conjunto declarado por las unidades.

    Solo actúa en multiunidad y sobre una copia. Conserva cualquier principal
    perteneciente al conjunto, y no elige otra forma en lugar del modelo.
    Las unidades y el contrato público mantienen su validación estricta.
    """
    if not isinstance(data, dict):
        return data
    units, labels = data.get("units"), data.get("classification")
    if not isinstance(units, list) or len(units) < 2 or not isinstance(labels, dict) or "main_form" not in labels:
        return data
    main = labels["main_form"]
    if main is not None and not isinstance(main, str):
        return data
    present = set()
    for unit in units:
        if not isinstance(unit, dict) or not isinstance(unit.get("classification"), dict):
            return data
        forms = unit["classification"].get("forms")
        if not isinstance(forms, list) or not forms or any(not isinstance(v, str) for v in forms):
            return data
        present.update(forms)
    if main in present or main is None and labels.get("main_form_reason") is None:
        return data
    result = deepcopy(data)
    result["classification"].update(main_form=None, main_form_reason=None)
    return result


def complete_llm_classification(data, *, expected_intervention_id, expected_text, allowed_context_turn_ids=()):
    """Validar el protocolo nuevo y restaurar la proyección pública compatible."""
    data = _complete_missing_global_approach_reason(data)
    data = _normalize_global_main_form(data)
    try:
        schema = classification_llm_schema()
        if isinstance(data, dict) and isinstance(data.get("units"), list):
            count = len(data["units"])
            branch = schema.pop("oneOf")[0 if count == 0 else 1 if count == 1 else 2]
            for key, value in branch["properties"].items():
                if key == "units":
                    schema["properties"][key].update(value)
                else:
                    schema["properties"][key] = value
        validate_data(data, schema, detailed_errors=True)
    except DataValidationError as error:
        raise ClassificationContractError(error.path, error.rule, error.detail) from None
    if data["intervention_id"] != expected_intervention_id or data["original_text"] != expected_text:
        raise ClassificationContractError("/", "source_identity", "La identidad o el texto no coincide con la entrada original.")
    result = deepcopy(data)
    spans = locate_quotes(expected_text, [unit["quote"] for unit in result["units"]])
    for unit, (start, end) in zip(result["units"], spans):
        unit.update(text=unit.pop("quote"), source_start=start, source_end=end)
    result = build_derived_labels(result)
    result["contract_version"] = "1.0.0"
    return validate_classification_expectation(result, expected_intervention_id=expected_intervention_id,
        expected_text=expected_text, allowed_context_turn_ids=allowed_context_turn_ids)

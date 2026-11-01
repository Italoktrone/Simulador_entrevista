"""Casos de referencia vinculados al perfil; no evalúa respuestas de un LLM."""

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from harness.interview_config import InterviewSetup, load_interview_setup
from harness.json_loader import load_json, load_json_with_bytes
from harness.schema_validator import validate_data
from harness.temporal_facts import build_temporal_facts


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE_PATH = PROJECT_ROOT / "data/reference_questions/consistencia_basica.json"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas/reference_suite.schema.json"


class ReferenceSuiteError(ValueError):
    """El conjunto no es válido o no corresponde al escenario revisado."""


def resolve_source_path(source: object, path: list) -> object:
    """Resolver claves e índices explícitos, sin interpretar rutas de archivos."""
    if not isinstance(path, list) or not path:
        raise ReferenceSuiteError("La referencia necesita una lista no vacía de claves o índices.")
    node = source
    for key in path:
        if isinstance(node, dict) and isinstance(key, str) and key in node:
            node = node[key]
        elif isinstance(node, list) and type(key) is int and 0 <= key < len(node):
            node = node[key]
        else:
            raise ReferenceSuiteError("Una referencia apunta a un campo o índice inexistente.")
    return deepcopy(node)


def prepare_reference_cases(data: dict, schema: dict, setup: InterviewSetup) -> list[dict]:
    """Validar contratos y referencias y devolver copias con hechos resueltos.

    Recibe un escenario ya validado. Los valores esperados proceden de sus
    fuentes; nunca se obtienen del proveedor o de una respuesta del candidato.
    """
    try:
        validate_data(data, schema)
    except ValueError:
        raise ReferenceSuiteError("El conjunto de referencia no cumple su esquema.") from None
    profile = setup.candidate.to_dict()
    if (data["candidate_id"] != setup.candidate.candidate_id or data["job_id"] != setup.config_dict()["job_id"] or
            data["scenario_reference_date"] != setup.candidate.scenario_reference_date):
        raise ReferenceSuiteError("Las referencias del conjunto no coinciden con el escenario cargado.")
    if data["candidate_source_sha256"] != setup.candidate.source_sha256:
        raise ReferenceSuiteError("La huella del perfil no coincide con la fuente revisada del conjunto.")
    sources = {"candidate_profile": profile, "temporal_facts": build_temporal_facts(profile)}
    seen_cases = set()
    resolved = []
    for case in data["cases"]:
        if case["case_id"] in seen_cases:
            raise ReferenceSuiteError("Los identificadores de caso no pueden repetirse.")
        seen_cases.add(case["case_id"])
        if len(case["steps"]) > setup.config_dict()["max_questions"]:
            raise ReferenceSuiteError("Un caso supera el límite de preguntas configurado para su sesión.")
        facts = {}
        for fact in case["reference_facts"]:
            if fact["fact_id"] in facts:
                raise ReferenceSuiteError("Los identificadores de hechos no pueden repetirse dentro de un caso.")
            facts[fact["fact_id"]] = {**deepcopy(fact), "value": resolve_source_path(sources[fact["source"]], fact["path"])}
        used = set()
        for number, step in enumerate(case["steps"], 1):
            if step["step_number"] != number:
                raise ReferenceSuiteError("Los pasos deben numerarse consecutivamente desde uno.")
            if any(identifier not in facts for identifier in step["expected_fact_ids"]):
                raise ReferenceSuiteError("Un paso cita un hecho que no existe en su caso.")
            used.update(step["expected_fact_ids"])
        if used != set(facts):
            raise ReferenceSuiteError("El caso contiene hechos que no se utilizan en sus pasos.")
        resolved.append({**deepcopy(case), "reference_facts": list(facts.values())})
    return resolved


@dataclass(frozen=True, slots=True)
class ReferenceSuite:
    source_path: Path
    source_sha256: str
    _snapshot_json: str = field(repr=False)
    _resolved_json: str = field(repr=False)

    @property
    def suite_id(self) -> str:
        return self.to_dict()["suite_id"]

    def to_dict(self) -> dict:
        return json.loads(self._snapshot_json)

    def resolved_cases(self) -> list[dict]:
        return json.loads(self._resolved_json)


def load_reference_suite(
    path: str | Path = DEFAULT_SUITE_PATH, *, setup: InterviewSetup | None = None,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> ReferenceSuite:
    setup = load_interview_setup() if setup is None else setup
    setup.candidate.assert_source_unchanged()
    try:
        data, raw = load_json_with_bytes(path)
        schema = load_json(schema_path)
    except ValueError:
        raise ReferenceSuiteError("No se pudieron leer el conjunto y su esquema JSON local.") from None
    resolved = prepare_reference_cases(data, schema, setup)
    setup.candidate.assert_source_unchanged()
    return ReferenceSuite(
        source_path=Path(path).resolve(), source_sha256=hashlib.sha256(raw).hexdigest().upper(),
        _snapshot_json=json.dumps(data, ensure_ascii=False, allow_nan=False),
        _resolved_json=json.dumps(resolved, ensure_ascii=False, allow_nan=False),
    )

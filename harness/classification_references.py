"""Carga y validación de referencias aprobadas; no clasifica ni evalúa un LLM."""

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from harness.classification_contract import validate_classification_expectation
from harness.json_loader import load_json, load_json_with_bytes
from harness.schema_validator import validate_data


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCES_PATH = ROOT / "data/reference_questions/clasificacion_basica.json"
REFERENCES_SCHEMA_PATH = ROOT / "schemas/classification_references.schema.json"
CONFIG_SCHEMA_PATH = ROOT / "schemas/interview_config.schema.json"
SPLITS = ("desarrollo", "comprobacion_conocida")


class ClassificationReferencesError(ValueError):
    """Referencias inválidas; los errores no copian textos ni datos rechazados."""


def prepare_classification_references(data: object) -> dict:
    """Comprobar envoltura, configuración, identidad, contexto y expectativas.

    Devuelve una copia. Los turnos se autorizan por caso; nunca se construye un
    historial compartido entre ejemplos ni se asigna un método de generación.
    """
    try:
        json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        validate_data(data, load_json(REFERENCES_SCHEMA_PATH))
        config_schema = load_json(CONFIG_SCHEMA_PATH)
        validate_data(data["base_configuration"], config_schema)
        result = deepcopy(data)
        split_counts = {split: 0 for split in SPLITS}
        for index, case in enumerate(result["cases"], 1):
            if case["case_id"] != f"R{index:02}":
                raise ValueError("case_sequence")
            split_counts[case["split"]] += 1
            configuration = result["base_configuration"] | case["input"]["configuration_overrides"]
            validate_data(configuration, config_schema)
            turn_ids = tuple(turn["turn_number"] for turn in case["input"]["context_turns"])
            if (any(type(number) is not int or number >= configuration["max_questions"] for number in turn_ids)
                    or tuple(sorted(set(turn_ids))) != turn_ids):
                raise ValueError("context_sequence")
            if case["expected"].get("contract_version") != result["classification_contract_version"]:
                raise ValueError("contract_version")
            case["expected"] = validate_classification_expectation(
                case["expected"], expected_intervention_id=case["case_id"],
                expected_text=case["input"]["text"], allowed_context_turn_ids=turn_ids,
            )
        if split_counts != {"desarrollo": 30, "comprobacion_conocida": 10}:
            raise ValueError("split_counts")
    except (ValueError, TypeError, KeyError, RecursionError, UnicodeError):
        raise ClassificationReferencesError(
            "El conjunto no cumple su esquema, las expectativas o las relaciones entre casos y contexto."
        ) from None
    return result


@dataclass(frozen=True, slots=True)
class ClassificationReferenceSuite:
    source_path: Path
    source_sha256: str
    _snapshot_json: str = field(repr=False)

    def to_dict(self) -> dict:
        """Copia completa para auditoría; no se entrega al clasificador."""
        return json.loads(self._snapshot_json)

    def cases(self, *, split: str = "desarrollo") -> list[dict]:
        """Por defecto expone solo desarrollo; comprobación se solicita explícitamente."""
        if split not in SPLITS:
            raise ValueError("Elige desarrollo o comprobacion_conocida.")
        return [case for case in self.to_dict()["cases"] if case["split"] == split]

    def input_for(self, case_id: str, *, split: str = "desarrollo") -> dict:
        """Entrada independiente sin etiquetas, dificultad ni notas de anotación.

        La selección de comprobación requiere split explícito. Esta entrada
        aún no es un prompt ni llama al clasificador.
        """
        data = self.to_dict()
        for case in self.cases(split=split):
            if case["case_id"] == case_id:
                return {
                    "intervention_id": case_id, "text": case["input"]["text"],
                    "configuration": data["base_configuration"] | case["input"]["configuration_overrides"],
                    "context_turns": case["input"]["context_turns"],
                    "competency": case["input"]["competency"],
                }
        raise ValueError("El caso no pertenece al grupo solicitado.")


def load_classification_references(path: str | Path = DEFAULT_REFERENCES_PATH) -> ClassificationReferenceSuite:
    """Leer una vez con el cargador JSON estricto y conservar una instantánea."""
    try:
        data, raw = load_json_with_bytes(path)
        prepared = prepare_classification_references(data)
        snapshot = json.dumps(prepared, ensure_ascii=False, allow_nan=False)
    except ValueError:
        raise ClassificationReferencesError("No se pudo cargar un conjunto de clasificación válido.") from None
    return ClassificationReferenceSuite(
        source_path=Path(path).resolve(), source_sha256=hashlib.sha256(raw).hexdigest().upper(),
        _snapshot_json=snapshot,
    )

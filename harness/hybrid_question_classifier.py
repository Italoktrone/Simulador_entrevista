"""Coordinación local -> LLM, sin repetir clasificación ni cambiar etiquetas."""

from copy import deepcopy
from dataclasses import dataclass, field
import json

from harness.llm_question_classifier import LLMQuestionClassifier
from harness.question_classifier import classify_local


HYBRID_CLASSIFIER_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class HybridClassification:
    """Un resultado validado, con su ruta y auditoría fuera del contrato de etiquetas."""

    route: str
    _result_json: str = field(repr=False)
    _trace_json: str = field(repr=False)
    classifier_version: str = HYBRID_CLASSIFIER_VERSION

    @property
    def result(self) -> dict:
        return json.loads(self._result_json)

    @property
    def trace(self) -> dict:
        return json.loads(self._trace_json)

    @property
    def status(self) -> str:
        return "respaldo" if self.result["technical_error"] is not None else "clasificada"

    def to_dict(self) -> dict:
        return {
            "classifier_version": self.classifier_version,
            "strategy": "reglas_luego_llm", "route": self.route, "status": self.status,
            "result": self.result, "trace": self.trace,
        }


class HybridQuestionClassifier:
    """Reutiliza los componentes que ya validan sus resultados.

    El intérprete se inyecta; aquí no se construyen clientes, leen claves o
    seleccionan modelos. No hay llamadas a generate ni bucles de reparación.
    """

    def __init__(self, llm_classifier: LLMQuestionClassifier):
        if not isinstance(llm_classifier, LLMQuestionClassifier):
            raise ValueError("Se requiere un LLMQuestionClassifier ya configurado.")
        self._llm = llm_classifier

    def classify(
        self, text: str, *, intervention_id: str, configuration: dict | None = None,
        context_turns: list[dict] | tuple[dict, ...] | None = None, competency: str | None = None,
    ) -> HybridClassification:
        """Una evaluación local; solo su abstención invoca una vez al intérprete.

        El resultado local indeterminado por ausencia de contexto es final:
        no se intenta recuperar antecedentes inexistentes mediante el modelo.
        La selección de contexto y política de respuesta pertenecen al llamador.
        """
        try:
            request = deepcopy({"text": text, "intervention_id": intervention_id,
                                "configuration": configuration, "context_turns": context_turns,
                                "competency": competency})
        except RecursionError:
            raise ValueError("La entrada tiene demasiados niveles de anidación.") from None

        # Los componentes conservan su validación de entrada y salida. La
        # auditoría no se utiliza como prompt ni como instrucciones al candidato.
        local = classify_local(**request)
        local_trace = local.to_dict()
        result = local_trace.pop("result")
        local_trace.pop("intervention_id")
        local_trace.pop("original_text")
        trace = {"local": local_trace, "llm": None}
        route = "reglas"
        if local.status == "abstencion":
            semantic = self._llm.classify(**request)
            semantic_trace = semantic.to_dict()
            result = semantic_trace.pop("result")
            trace["llm"] = semantic_trace
            route = "llm"

        # No se reetiqueta method=hibrido: la fuente efectiva de todas las
        # unidades es reglas o LLM. Un respaldo conserva su código técnico.
        return HybridClassification(
            route, json.dumps(result, ensure_ascii=False, allow_nan=False),
            json.dumps(trace, ensure_ascii=False, allow_nan=False),
        )

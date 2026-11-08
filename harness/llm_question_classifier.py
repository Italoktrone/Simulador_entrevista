"""Interpretación descriptiva por LLM, JSON estricto y recuperación acotada."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
from re import fullmatch

from jsonschema import Draft202012Validator

from harness.classification_contract import (
    ClassificationContractError, validate_classification,
)
from harness.llm_classification_contract import (
    classification_llm_schema, classification_generation_schema, complete_llm_classification,
)
from harness.classification_input import validate_classification_input
from harness.classification_aggregation import AGGREGATION_VERSION
from harness.llm_classification_contract import LLM_CONTRACT_VERSION
from harness.json_loader import JsonTextError, parse_json_text
from harness.llm.client import (
    LLMClient, LLMResponse, LLMAuthenticationError, LLMConnectionError,
    LLMContextLimitError, LLMInvalidResponseError, LLMModelNotFoundError,
    LLMProviderError, LLMTimeoutError, LLMError,
)
from harness.llm.factory import create_client
from harness.llm.ollama_client import OllamaClient
from harness.llm.messages import ChatMessage
from harness.validation_audit import ValidationAudit, safe_validation_audit
from harness.classifier_few_shot import load_few_shot, disabled_few_shot


CLASSIFIER_VERSION = "1.5.0"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "agent/classifier.md"
MAX_GENERATIONS = 2  # Primera salida y, solo si es JSON/contrato inválido, una reparación.


@dataclass(frozen=True, slots=True)
class ClassificationLLMSettings:
    """Parámetros de un cliente nuevo; nunca modifica al cliente del candidato."""

    model: str | None = None
    max_output_tokens: int = 2048

    def __post_init__(self):
        if self.model is not None and (not isinstance(self.model, str) or
                fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}", self.model) is None):
            raise ValueError("El modelo de clasificación debe ser un identificador sin espacios o None.")
        if type(self.max_output_tokens) is not int or not 16 <= self.max_output_tokens <= 4096:
            raise ValueError("El presupuesto de clasificación debe ser un entero entre 16 y 4096.")


def create_classification_client(environ=None, *, settings=None, transport=None, structured_output=True):
    """Reutilizar fábrica, autenticación y errores. Crear no envía solicitudes.

    model=None hereda la selección del proveedor en environ. Los 2048 tokens
    por defecto pertenecen solo al clasificador, sin incrementos tras fallos.
    Ollama recibe una plantilla en format por defecto; classify la restringe
    por solicitud a los turnos autorizados. El candidato
    conserva su salida libre. structured_output=False permite el diagnóstico
    comparativo autorizado; no relaja la validación ni aumenta reparaciones.
    El llamador administra el cierre del cliente con el mismo context manager.
    """
    settings = ClassificationLLMSettings() if settings is None else settings
    if not isinstance(settings, ClassificationLLMSettings):
        raise ValueError("Se requiere ClassificationLLMSettings.")
    if type(structured_output) is not bool:
        raise ValueError("structured_output debe ser booleano.")
    values = os.environ if environ is None else environ
    options = {}
    if structured_output and values.get("LLM_PROVIDER", "ollama") == "ollama":
        options["output_schema"] = classification_generation_schema()
    return create_client(environ, transport=transport, model=settings.model,
                         max_output_tokens=settings.max_output_tokens, **options)


@dataclass(frozen=True, slots=True)
class ClassificationAttempt:
    number: int
    status: str
    error_code: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    elapsed_seconds: float | None = None
    finish_reason: str | None = None
    validation_error: ValidationAudit | None = None


@dataclass(frozen=True, slots=True)
class LLMClassification:
    attempts: tuple[ClassificationAttempt, ...]
    prompt_sha256: str
    _result_json: str = field(repr=False)
    classifier_version: str = CLASSIFIER_VERSION
    _few_shot_json: str = field(default_factory=lambda: json.dumps(disabled_few_shot()), repr=False)

    @property
    def result(self) -> dict:
        return json.loads(self._result_json)

    @property
    def status(self) -> str:
        return "respaldo" if self.result["technical_error"] is not None else "clasificada"

    def to_dict(self) -> dict:
        return {"classifier_version": self.classifier_version, "prompt_sha256": self.prompt_sha256,
                "llm_contract_version": LLM_CONTRACT_VERSION, "aggregation_version": AGGREGATION_VERSION,
                "aggregation_applied": self.status == "clasificada" and self.result["evaluability"] == "evaluable",
                "few_shot": json.loads(self._few_shot_json),
                "status": self.status, "attempts": [asdict(attempt) for attempt in self.attempts],
                "result": self.result}


def _audit(number, status, error_code=None, response=None, validation_error=None) -> ClassificationAttempt:
    if not isinstance(response, LLMResponse):
        return ClassificationAttempt(number, status, error_code)
    def count(value):
        return value if type(value) is int and value >= 0 else None
    elapsed = response.elapsed_seconds
    elapsed = elapsed if type(elapsed) in (int, float) and isfinite(elapsed) and elapsed >= 0 else None
    reason = response.finish_reason
    reason = reason if reason in (None, "stop", "completed", "length") else "otro"
    return ClassificationAttempt(number, status, error_code, count(response.input_tokens),
                                 count(response.output_tokens), elapsed, reason, validation_error)


def _provider_code(error: Exception) -> str:
    for error_type, code in (
        (LLMAuthenticationError, "authentication_error"), (LLMTimeoutError, "timeout"),
        (LLMConnectionError, "connection_error"), (LLMContextLimitError, "context_limit"),
        (LLMModelNotFoundError, "model_not_found"), (LLMInvalidResponseError, "invalid_response"),
        (LLMProviderError, "provider_error"), (LLMError, "llm_error"),
    ):
        if isinstance(error, error_type):
            return code
    return "unexpected_provider_error"


def _repair_instruction(error: ClassificationContractError, audit: ValidationAudit, allowed_ids: tuple[int, ...]) -> str:
    """Instrucciones del programa; nunca reinyecta contenido rechazado."""
    context_hint = (
        "context_turn_ids solo puede contener turnos de " + json.dumps(list(allowed_ids))
        + ". Si no utilizas contexto, devuelve []. followup_of debe ser null sin vínculo confirmado; "
        "si hay vínculo, debe ser un entero autorizado incluido también en context_turn_ids. "
        "context_status=no_necesario exige followup_of=null. No inventes ni renumeres turnos."
    )
    hint = {
        "quote_not_found": "quote debe ser una copia literal y contigua de input.text.",
        "quote_order": "Ordena los quote sin solapamiento, siguiendo input.text.",
        "quote_ambiguous": "Amplía los quote para que su posición en input.text sea inequívoca.",
        "dominance_reason": (
            "Con una sola etiqueta o sin principal, main_approach_reason y main_form_reason deben ser null. "
            "Con varias etiquetas y un principal seleccionado, escribe una razón no vacía que explique esa prioridad. "
            "La explicación general de las etiquetas va en rationale, que nunca debe estar vacío."
        ),
    }.get(error.rule)
    if error.rule in {"context_scope", "integer_identity", "followup_scope", "followup_context", "context_evidence"}:
        hint = context_hint
    elif error.rule in {"minLength", "pattern"} and audit.path.endswith("/rationale"):
        hint = "Escribe en ese rationale una justificación breve, no vacía ni de solo espacios, basada en la petición. No la omitas."
    elif error.rule == "maxLength" and audit.path.endswith("/rationale"):
        hint = "Escribe una sola frase de hasta 160 caracteres en ese rationale. No trunques citas ni cambies las etiquetas para abreviar."
    elif audit.path.startswith("/classification") and error.rule != "dominance_reason":
        hint = "Con una sola unidad devuelve classification={}; Python copia sus principales y justificación. Con varias, conserva las decisiones globales y razones de predominio válidas."
    if hint is None:
        hint = "Respeta los campos, enums, conjuntos únicos y relaciones definidos, sin inventar otros."
    return "Campo detectado: " + json.dumps(audit.path) + ". " + hint


def _completed_result(draft: dict, request: dict, allowed_ids: tuple[int, ...]) -> dict:
    draft = complete_llm_classification(
        draft, expected_intervention_id=request["intervention_id"], expected_text=request["text"],
        allowed_context_turn_ids=allowed_ids,
    )
    draft.update(method="llm", rule_ids=[], technical_error=None, validation_status="pendiente")
    for unit in draft["units"]:
        unit.update(method="llm", rule_ids=[])
    return validate_classification(
        draft, expected_intervention_id=request["intervention_id"], expected_text=request["text"],
        allowed_context_turn_ids=allowed_ids,
    )


def _fallback(request: dict, error_code: str, allowed_ids: tuple[int, ...]) -> dict:
    reason = "No se obtuvo una clasificación válida por un fallo técnico; no se infiere evaluabilidad."
    return validate_classification({
        "contract_version": "1.0.0", "intervention_id": request["intervention_id"],
        "original_text": request["text"], "evaluability": None, "non_evaluable_reason": None,
        "classification": {
            "approaches": ["indeterminado"], "main_approach": "indeterminado",
            "secondary_approaches": [], "main_approach_reason": None,
            "forms": ["indeterminada"], "main_form": "indeterminada", "main_form_reason": None,
            "attributes": [], "certainty": "indeterminada", "rationale": reason,
        },
        "units": [], "context_turn_ids": [], "method": "respaldo", "rule_ids": [],
        "technical_error": error_code, "validation_status": "pendiente", "rationale": reason,
    }, expected_intervention_id=request["intervention_id"], expected_text=request["text"],
       allowed_context_turn_ids=allowed_ids)


class LLMQuestionClassifier:
    """Cliente inyectado y contexto ya seleccionado; no ejecuta reglas ni runtime."""

    def __init__(self, client: LLMClient, *, instructions: str | None = None, few_shot: bool = True):
        if not callable(getattr(client, "generate", None)):
            raise ValueError("Se requiere un cliente LLM con generate.")
        if instructions is None:
            try:
                instructions = PROMPT_PATH.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                raise ValueError("No se pudieron cargar las instrucciones del clasificador.") from None
        if not isinstance(instructions, str) or not instructions.strip():
            raise ValueError("Las instrucciones confiables deben ser texto no vacío.")
        schema = classification_llm_schema()
        Draft202012Validator.check_schema(schema)
        if type(few_shot) is not bool:
            raise ValueError("few_shot debe ser booleano.")
        examples, metadata = load_few_shot() if few_shot else ("", disabled_few_shot())
        self._few_shot_json = json.dumps(metadata, ensure_ascii=False)
        self._system = instructions + examples + "\n\nESQUEMA_DE_ETIQUETAS_JSON:\n" + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        self._client = client

    def classify(
        self, text: str, *, intervention_id: str, configuration: dict | None = None,
        context_turns: list[dict] | tuple[dict, ...] | None = None, competency: str | None = None,
    ) -> LLMClassification:
        allowed_ids = validate_classification_input(
            intervention_id, text, configuration, () if context_turns is None else context_turns, competency,
        )
        request = deepcopy({"intervention_id": intervention_id, "text": text, "configuration": configuration,
                            "context_turns": [] if context_turns is None else context_turns, "competency": competency})
        payload = json.dumps({"input": request}, ensure_ascii=False, separators=(",", ":"))
        generation_schema = classification_generation_schema(allowed_context_turn_ids=allowed_ids)
        system = self._system + (
            "\n\nTURNOS_AUTORIZADOS_PARA_ESTA_INTERVENCION: " + json.dumps(list(allowed_ids))
            + ". context_turn_ids solo puede ser un subconjunto de esta lista, nunca números de intervenciones. "
            "Sin turnos disponibles, devuelve context_turn_ids=[] y followup_of=null. "
            "Con turnos disponibles, usa [] y null si la pregunta no necesita contexto. "
            "No inventes ni renumeres referencias."
        )
        prompt_sha256 = hashlib.sha256(system.encode("utf-8")).hexdigest().upper()
        attempts = []
        last_error = None
        repair_hint = ""

        def finish(result):
            return LLMClassification(tuple(attempts), prompt_sha256,
                                     json.dumps(result, ensure_ascii=False, allow_nan=False), _few_shot_json=self._few_shot_json)

        for number in range(1, MAX_GENERATIONS + 1):
            validation_error = None
            repair = "" if last_error is None else (
                "\n\nREPARACION_CONTROLADA: La salida anterior incumplió " + last_error
                + ". Regenera una sola respuesta JSON completa desde los datos originales y el esquema. "
                "No añadas prosa ni campos de ejecución. Esta es la única reparación permitida. " + repair_hint
            )
            # No se reinyecta la salida rechazada ni se promueve historial a system.
            messages: list[ChatMessage] = [
                {"role": "system", "content": system + repair},
                {"role": "user", "content": payload},
            ]
            try:
                if isinstance(self._client, OllamaClient) and self._client.structured_output_enabled:
                    response = self._client.generate(messages, output_schema=generation_schema)
                else:
                    response = self._client.generate(messages)
            except Exception as error:
                attempts.append(_audit(number, "error_proveedor", _provider_code(error)))
                return finish(_fallback(request, "error_proveedor", allowed_ids))
            if not isinstance(response, LLMResponse):
                attempts.append(_audit(number, "error_proveedor", "invalid_response"))
                return finish(_fallback(request, "error_proveedor", allowed_ids))
            final = response.finish_reason in (None, "stop") or (
                response.provider == "openai" and response.finish_reason == "completed"
            )
            if not final:
                code = "output_limit" if response.finish_reason == "length" else "unexpected_finish"
                attempts.append(_audit(number, "error_proveedor", code, response))
                return finish(_fallback(request, "error_proveedor", allowed_ids))
            try:
                draft = parse_json_text(response.text)
            except JsonTextError:
                last_error = "json_invalido"
            else:
                try:
                    result = _completed_result(draft, request, allowed_ids)
                except ClassificationContractError as error:
                    last_error = "contrato_invalido"
                    validation_error = safe_validation_audit(error)
                    repair_hint = "Regla: " + validation_error.rule + ". " + _repair_instruction(error, validation_error, allowed_ids)
                else:
                    attempts.append(_audit(number, "validada", response=response))
                    return finish(result)
            attempts.append(_audit(number, last_error, last_error, response, validation_error))
        return finish(_fallback(request, last_error, allowed_ids))

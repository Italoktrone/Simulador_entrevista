"""Adaptador síncrono para /api/chat del servicio Ollama local."""

from time import perf_counter
from math import isfinite
import json
import re
from typing import Self

import httpx
from jsonschema import Draft202012Validator, SchemaError

from harness.llm.client import (
    LLMConnectionError,
    LLMContextLimitError,
    LLMInvalidResponseError,
    LLMModelNotFoundError,
    LLMProviderError,
    LLMResponse,
    LLMTimeoutError,
)
from harness.llm.config import OllamaSettings
from harness.llm.messages import ChatMessage, validate_messages


def _token_count(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _seconds_from_nanoseconds(value: object) -> float | None:
    if type(value) is not int or value < 0:
        return None
    try:
        seconds = value / 1_000_000_000
    except OverflowError:
        return None
    return seconds if isfinite(seconds) else None


def _is_context_limit(data: object) -> bool:
    """Reconocer formas conocidas sin copiar texto del servidor al error público.

    Ollama 0.34.2 puede envolver el error tipado del motor en un string JSON.
    Se permite una sola envoltura; otros errores conservan su tratamiento genérico.
    """
    if not isinstance(data, dict):
        return False
    error = data.get("error")
    if isinstance(error, str):
        if error == "the input length exceeds the context length" or re.fullmatch(
            r"request \([0-9]+ tokens\) exceeds the available context size \([0-9]+ tokens\)(?:, try increasing it)?", error
        ):
            return True
        try:
            nested = json.loads(error)
        except (ValueError, RecursionError):
            return False
        error = nested.get("error") if isinstance(nested, dict) else None
    return isinstance(error, dict) and error.get("type") == "exceed_context_size_error"


def _context_limit_error() -> LLMContextLimitError:
    return LLMContextLimitError(
        "Ollama rechazó la solicitud por falta de espacio de contexto. "
        "No se repitió la generación ni se cambió la capacidad configurada."
    )


def _model_messages(model: str, messages: list[ChatMessage]) -> list[ChatMessage]:
    """Gemma 3n no tiene turno system nativo: fusionar solo el par inicial.

    La plantilla distribuida convierte system en user. Enviar ambos separados
    produce dos turnos user consecutivos. Se conserva el contrato general y el
    texto original de la pregunta; esta adaptación pertenece solo al transporte.
    """
    if (
        model.split(":", 1)[0] == "gemma3n"
        and len(messages) >= 2
        and messages[0]["role"] == "system"
        and messages[1]["role"] == "user"
    ):
        return [{
            "role": "user",
            "content": messages[0]["content"]
            + "\n\nPREGUNTA_DEL_ENTREVISTADOR (entrada de conversación):\n"
            + messages[1]["content"],
        }, *[dict(message) for message in messages[2:]]]
    return [dict(message) for message in messages]


class OllamaClient:
    """Conexión local sin proxies del entorno, redirecciones ni fallback externo."""

    provider = "ollama"

    def __init__(
        self,
        settings: OllamaSettings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        output_schema: dict | None = None,
    ) -> None:
        self.settings = settings if settings is not None else OllamaSettings()
        self._output_schema_json = None
        if output_schema is not None:
            try:
                if not isinstance(output_schema, dict):
                    raise ValueError
                encoded = json.dumps(output_schema, ensure_ascii=False, allow_nan=False)
                encoded.encode("utf-8")
                Draft202012Validator.check_schema(output_schema)
                # Instantánea independiente de mutaciones externas del esquema.
                self._output_schema_json = encoded
            except (ValueError, TypeError, RecursionError, UnicodeError, SchemaError):
                raise ValueError("output_schema debe ser un JSON Schema válido y serializable.") from None
        self._http = httpx.Client(
            base_url=self.settings.base_url.rstrip("/"),
            timeout=httpx.Timeout(
                self.settings.read_timeout_seconds,
                connect=self.settings.connect_timeout_seconds,
                write=10.0,
                pool=5.0,
            ),
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    @property
    def structured_output_enabled(self) -> bool:
        return self._output_schema_json is not None

    def generate(self, messages: list[ChatMessage], *, output_schema: dict | None = None) -> LLMResponse:
        validate_messages(messages)
        schema_json = self._output_schema_json
        if output_schema is not None:
            # Copia por solicitud: nunca modifica el formato del cliente
            # compartido ni hereda IDs de una intervención anterior.
            try:
                if not isinstance(output_schema, dict):
                    raise ValueError
                schema_json = json.dumps(output_schema, ensure_ascii=False, allow_nan=False)
                schema_json.encode("utf-8")
                Draft202012Validator.check_schema(output_schema)
            except (ValueError, TypeError, RecursionError, UnicodeError, SchemaError):
                raise ValueError("output_schema debe ser un JSON Schema válido y serializable.") from None
        payload = {
            "model": self.settings.model,
            "messages": _model_messages(self.settings.model, messages),
            "stream": False,
            "think": False,
            "truncate": False,
            "shift": False,
            "keep_alive": self.settings.keep_alive,
            "options": {
                "num_ctx": self.settings.context_size,
                "num_predict": self.settings.max_output_tokens,
                "temperature": self.settings.temperature,
            },
        }
        if schema_json is not None:
            payload["format"] = json.loads(schema_json)
        started = perf_counter()
        for attempt in range(self.settings.connection_retries + 1):
            try:
                response = self._http.post("/api/chat", json=payload)
                break
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                if attempt < self.settings.connection_retries:
                    continue
                error = LLMTimeoutError if isinstance(exc, httpx.ConnectTimeout) else LLMConnectionError
                raise error("No se pudo conectar con Ollama. Comprueba que el servicio esté abierto.") from exc
            except httpx.TimeoutException as exc:
                # No repetir una generación que podría seguir ejecutándose en el servidor.
                raise LLMTimeoutError(
                    "Ollama superó el tiempo de espera. No se repitió la generación."
                ) from exc
            except httpx.RequestError as exc:
                raise LLMConnectionError("Falló la comunicación con Ollama.") from exc

        if response.status_code == 404:
            raise LLMModelNotFoundError(
                "Ollama no encontró el modelo. Comprueba su nombre con ollama list."
            )
        if not 200 <= response.status_code < 300:
            if response.status_code == 400:
                try:
                    error_data = response.json()
                except (ValueError, RecursionError):
                    error_data = None
                if _is_context_limit(error_data):
                    raise _context_limit_error()
            raise LLMProviderError(f"Ollama rechazó la solicitud (HTTP {response.status_code}).")
        try:
            data = response.json()
        except (ValueError, RecursionError) as exc:
            raise LLMInvalidResponseError("Ollama no devolvió un JSON válido.") from exc
        if not isinstance(data, dict):
            raise LLMInvalidResponseError("La respuesta de Ollama debe ser un objeto JSON.")
        if "error" in data:
            if _is_context_limit(data):
                raise _context_limit_error()
            raise LLMProviderError("Ollama comunicó un error al generar la respuesta.")
        message = data.get("message")
        model = data.get("model")
        if (
            data.get("done") is not True
            or not isinstance(model, str)
            or not model.strip()
            or not isinstance(message, dict)
            or message.get("role") != "assistant"
            or not isinstance(message.get("content"), str)
            or not message["content"].strip()
        ):
            raise LLMInvalidResponseError("Ollama devolvió una respuesta incompleta o sin texto del candidato.")
        if "<think>" in message["content"] or "</think>" in message["content"]:
            raise LLMInvalidResponseError(
                "Ollama mezcló marcas de razonamiento con la respuesta. Revisa la plantilla del modelo."
            )
        reason = data.get("done_reason")
        input_tokens = _token_count(data.get("prompt_eval_count"))
        cached_tokens = _token_count(data.get("prompt_eval_cached_count"))
        if input_tokens is not None and cached_tokens is not None and cached_tokens > input_tokens:
            cached_tokens = None
        return LLMResponse(
            text=message["content"].strip(),
            model=model,
            provider="ollama",
            elapsed_seconds=perf_counter() - started,
            input_tokens=input_tokens,
            output_tokens=_token_count(data.get("eval_count")),
            finish_reason=reason if isinstance(reason, str) else None,
            server_total_seconds=_seconds_from_nanoseconds(data.get("total_duration")),
            load_seconds=_seconds_from_nanoseconds(data.get("load_duration")),
            prompt_eval_seconds=_seconds_from_nanoseconds(data.get("prompt_eval_duration")),
            eval_seconds=_seconds_from_nanoseconds(data.get("eval_duration")),
            cached_input_tokens=cached_tokens,
        )

"""Adaptador opcional de texto para la API Responses, sin SDK adicional."""

from time import perf_counter
from typing import Self

import httpx

from harness.llm.client import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMInvalidResponseError,
    LLMModelNotFoundError,
    LLMProviderError,
    LLMResponse,
    LLMTimeoutError,
)
from harness.llm.config import LLMConfigurationError, OpenAISettings
from harness.llm.messages import ChatMessage, validate_messages


def _token_count(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


class OpenAIClient:
    """Solo hace solicitudes al invocar generate; la clave queda fuera de settings."""

    provider = "openai"

    def __init__(
        self,
        settings: OpenAISettings,
        *,
        api_key: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if (
            not isinstance(api_key, str)
            or not api_key
            or any(ord(character) < 33 or ord(character) > 126 for character in api_key)
        ):
            raise LLMConfigurationError("OPENAI_API_KEY falta o contiene caracteres no admitidos.")
        self.settings = settings
        self._http = httpx.Client(
            base_url="https://api.openai.com/v1/",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(
                settings.read_timeout_seconds,
                connect=settings.connect_timeout_seconds,
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

    def generate(self, messages: list[ChatMessage]) -> LLMResponse:
        validate_messages(messages)
        payload = {
            "model": self.settings.model,
            "input": messages,
            "max_output_tokens": self.settings.max_output_tokens,
            "store": False,
            "stream": False,
        }
        started = perf_counter()
        for attempt in range(self.settings.connection_retries + 1):
            try:
                response = self._http.post("responses", json=payload)
                break
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                if attempt < self.settings.connection_retries:
                    continue
                error = LLMTimeoutError if isinstance(exc, httpx.ConnectTimeout) else LLMConnectionError
                raise error("No se pudo conectar con la API externa.") from None
            except httpx.TimeoutException:
                raise LLMTimeoutError(
                    "La API externa superó el tiempo de espera. No se repitió la generación."
                ) from None
            except httpx.RequestError:
                raise LLMConnectionError("Falló la comunicación con la API externa.") from None

        if response.status_code in (401, 403):
            raise LLMAuthenticationError("La API externa rechazó las credenciales o permisos.")
        if response.status_code == 404:
            raise LLMModelNotFoundError("El modelo externo no está disponible para esta solicitud.")
        if response.status_code == 429:
            raise LLMProviderError("La API externa informó un límite de uso o cuota (HTTP 429).")
        if not 200 <= response.status_code < 300:
            raise LLMProviderError(f"La API externa rechazó la solicitud (HTTP {response.status_code}).")
        try:
            data = response.json()
        except (ValueError, RecursionError):
            raise LLMInvalidResponseError("La API externa no devolvió un JSON válido.") from None
        if not isinstance(data, dict):
            raise LLMInvalidResponseError("La respuesta externa debe ser un objeto JSON.")
        if data.get("error") is not None:
            raise LLMProviderError("La API externa comunicó un error al generar la respuesta.")
        if data.get("status") != "completed":
            raise LLMInvalidResponseError("La API externa no completó la respuesta. No se acepta texto parcial.")
        model = data.get("model")
        output = data.get("output")
        if not isinstance(model, str) or not model.strip() or not isinstance(output, list):
            raise LLMInvalidResponseError("La respuesta externa no tiene el formato esperado.")

        parts = []
        for item in output:
            if not isinstance(item, dict):
                raise LLMInvalidResponseError("La respuesta externa contiene una salida inválida.")
            if item.get("type") == "reasoning":
                continue
            if (
                item.get("type") != "message"
                or item.get("role") != "assistant"
                or item.get("status") != "completed"
                or not isinstance(item.get("content"), list)
            ):
                raise LLMInvalidResponseError("La API externa no devolvió solo mensajes completos de texto.")
            for block in item["content"]:
                if (
                    not isinstance(block, dict)
                    or block.get("type") != "output_text"
                    or not isinstance(block.get("text"), str)
                    or not block["text"].strip()
                ):
                    raise LLMInvalidResponseError("La API externa no devolvió texto de candidato válido.")
                parts.append(block["text"])
        text = "\n".join(parts).strip()
        if not text or "<think>" in text or "</think>" in text:
            raise LLMInvalidResponseError("La respuesta externa está vacía o mezcla marcas de razonamiento.")
        usage = data.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        return LLMResponse(
            text=text,
            model=model,
            provider=self.provider,
            elapsed_seconds=perf_counter() - started,
            input_tokens=_token_count(usage.get("input_tokens")),
            output_tokens=_token_count(usage.get("output_tokens")),
            finish_reason=data["status"],
        )

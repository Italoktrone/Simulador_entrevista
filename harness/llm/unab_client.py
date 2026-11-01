"""Adaptador Chat Completions para UNAB IA; clave fuera de settings y registros."""

from dataclasses import dataclass
from copy import deepcopy
from time import perf_counter

import httpx

from harness.llm.config import LLMConfigurationError, OpenAISettings
from harness.llm.openai_client import OpenAIClient, _token_count
from harness.llm.messages import validate_messages
from harness.llm.client import (
    LLMAuthenticationError, LLMConnectionError, LLMInvalidResponseError,
    LLMModelNotFoundError, LLMProviderError, LLMResponse, LLMTimeoutError,
)


@dataclass(frozen=True)
class UNABSettings(OpenAISettings):
    model: str = "gemma4:26b"
    max_output_tokens: int = 2048
    base_url: str = "https://quotas.devhub.cl/api/v1/"
    reasoning_effort: str | None = "none"

    def __post_init__(self):
        super().__post_init__()
        if self.max_output_tokens > 4096:
            raise LLMConfigurationError("El presupuesto de salida UNAB debe estar entre 16 y 4096 tokens.")
        if self.base_url != "https://quotas.devhub.cl/api/v1/":
            raise LLMConfigurationError("La dirección de UNAB IA no coincide con el servicio configurado.")
        if self.reasoning_effort is not None and self.reasoning_effort not in ("none", "low", "medium", "high"):
            raise LLMConfigurationError("El esfuerzo de razonamiento de UNAB no es válido.")


class UNABClient(OpenAIClient):
    provider = "unab"

    def __init__(self, settings, *, api_key, transport=None):
        if not api_key:
            raise LLMConfigurationError("Falta api_key en config/llm.local.json para usar UNAB IA.")
        super().__init__(settings, api_key=api_key, transport=transport)
        self._http.base_url = settings.base_url
        self._call_diagnostics = []

    @property
    def call_diagnostics(self):
        """Solo metadatos permitidos; nunca clave, mensajes o razonamiento."""
        return deepcopy(self._call_diagnostics)

    def generate(self, messages):
        validate_messages(messages)
        payload = {"model": self.settings.model, "messages": messages,
                   "max_tokens": self.settings.max_output_tokens, "stream": False}
        if self.settings.reasoning_effort is not None:
            payload["reasoning_effort"] = self.settings.reasoning_effort
        diagnostic = {
            "call_number": len(self._call_diagnostics) + 1,
            "requested_max_tokens": self.settings.max_output_tokens,
            "requested_reasoning_effort": self.settings.reasoning_effort,
            "message_count": len(messages), "input_characters": sum(len(m["content"]) for m in messages),
            "http_status": None, "finish_reason": None, "validation_status": "not_completed",
            "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
            "reasoning_tokens": None, "cached_prompt_tokens": None,
            "content_characters": None, "reasoning_present": False,
        }
        self._call_diagnostics.append(diagnostic)
        started = perf_counter()
        for attempt in range(self.settings.connection_retries + 1):
            try:
                response = self._http.post("chat/completions", json=payload)
                break
            except (httpx.ConnectError, httpx.ConnectTimeout) as error:
                if attempt < self.settings.connection_retries:
                    continue
                cls = LLMTimeoutError if isinstance(error, httpx.ConnectTimeout) else LLMConnectionError
                raise cls("No se pudo conectar con UNAB IA.") from None
            except httpx.TimeoutException:
                raise LLMTimeoutError("UNAB IA superó el tiempo de espera. No se repitió la generación.") from None
            except httpx.RequestError:
                raise LLMConnectionError("Falló la comunicación con UNAB IA.") from None
        diagnostic["http_status"] = response.status_code
        if response.status_code in (401, 403):
            raise LLMAuthenticationError("UNAB IA rechazó las credenciales o permisos.")
        if response.status_code == 404:
            raise LLMModelNotFoundError("UNAB IA no encontró el endpoint o modelo solicitado.")
        if not 200 <= response.status_code < 300:
            raise LLMProviderError(f"UNAB IA rechazó la solicitud (HTTP {response.status_code}).")
        try:
            data = response.json()
        except (ValueError, RecursionError):
            raise LLMInvalidResponseError("UNAB IA no devolvió JSON válido.") from None
        if not isinstance(data, dict):
            raise LLMInvalidResponseError("UNAB IA devolvió un formato inesperado.")
        usage = data.get("usage")
        usage = usage if isinstance(usage, dict) else {}
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            diagnostic[field] = _token_count(usage.get(field))
        for source, field, target in (("completion_tokens_details", "reasoning_tokens", "reasoning_tokens"),
                                      ("prompt_tokens_details", "cached_tokens", "cached_prompt_tokens")):
            details = usage.get(source)
            if isinstance(details, dict):
                diagnostic[target] = _token_count(details.get(field))
        if data.get("error") is not None:
            raise LLMProviderError("UNAB IA comunicó un error al generar la respuesta.")
        choices = data.get("choices")
        model = data.get("model")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise LLMInvalidResponseError("UNAB IA no devolvió una única respuesta de texto.")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise LLMInvalidResponseError("UNAB IA no devolvió un mensaje válido.")
        text = message.get("content")
        reason = choice.get("finish_reason")
        diagnostic["finish_reason"] = reason if isinstance(reason, str) and reason in ("stop", "length", "tool_calls", "content_filter", "function_call") else "other"
        diagnostic["content_characters"] = len(text) if isinstance(text, str) else None
        diagnostic["reasoning_present"] = bool(message.get("reasoning") or message.get("reasoning_content") or message.get("thinking"))
        if reason == "length" and (text is None or isinstance(text, str) and not text.strip()):
            diagnostic["validation_status"] = "length_without_final_text"
            raise LLMInvalidResponseError(
                "UNAB IA alcanzó el límite de salida sin devolver texto final. Puede haber consumido tokens de razonamiento. "
                f"Presupuesto solicitado: {self.settings.max_output_tokens} tokens. "
                "No se repitió la llamada; se guardarán las métricas disponibles al cerrar la sesión."
            )
        if (not isinstance(model, str) or not model.strip() or message.get("role") != "assistant"
                or not isinstance(text, str) or not text.strip() or message.get("tool_calls")
                or message.get("function_call") or message.get("refusal")
                or not isinstance(reason, str) or reason not in {"stop", "length"}
                or any(marker in text for marker in ("<think>", "</think>", "<|channel>", "<channel|>"))):
            diagnostic["validation_status"] = "invalid_final_text"
            raise LLMInvalidResponseError(
                "UNAB IA no devolvió texto final de candidato válido. Se guardarán las métricas disponibles al cerrar la sesión."
            )
        diagnostic["validation_status"] = "truncated" if reason == "length" else "accepted"
        return LLMResponse(text=text.strip(), model=model, provider=self.provider,
                           elapsed_seconds=perf_counter() - started,
                           input_tokens=_token_count(usage.get("prompt_tokens")),
                           output_tokens=_token_count(usage.get("completion_tokens")), finish_reason=reason)

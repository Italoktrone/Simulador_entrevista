"""Selección explícita del proveedor; Ollama es el valor predeterminado."""

from collections.abc import Mapping
import os

import httpx

from harness.llm.config import LLMConfigurationError, OllamaSettings, OpenAISettings
from harness.llm.ollama_client import OllamaClient
from harness.llm.openai_client import OpenAIClient
from harness.llm.unab_client import UNABClient, UNABSettings


def create_client(
    environ: Mapping[str, str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
    model: str | None = None,
    max_output_tokens: int | None = None,
    output_schema: dict | None = None,
    read_timeout_seconds: float | None = None,
    connection_retries: int | None = None,
) -> OllamaClient | OpenAIClient | UNABClient:
    """Crear sin solicitudes; overrides explícitos solo afectan al cliente nuevo.

    Sin overrides conserva los valores del candidato. No lee archivos .env
    ni cambia de proveedor al fallar.
    """

    if max_output_tokens is not None and type(max_output_tokens) is not int:
        raise LLMConfigurationError("max_output_tokens debe ser un entero.")

    values = os.environ if environ is None else environ
    overrides = {}
    if read_timeout_seconds is not None:
        overrides["read_timeout_seconds"] = read_timeout_seconds
    if connection_retries is not None:
        overrides["connection_retries"] = connection_retries
    provider = values.get("LLM_PROVIDER", "ollama")
    if output_schema is not None and provider != "ollama":
        raise LLMConfigurationError("output_schema en format solo está implementado para Ollama.")
    if provider == "ollama":
        try:
            settings = OllamaSettings(
                model=model if model is not None else values.get("OLLAMA_MODEL", OllamaSettings().model),
                max_output_tokens=max_output_tokens if max_output_tokens is not None else OllamaSettings().max_output_tokens,
                **overrides,
            )
        except ValueError as error:
            raise LLMConfigurationError(f"OLLAMA_MODEL inválido: {error}") from error
        return OllamaClient(settings, transport=transport, output_schema=output_schema)
    if provider == "unab":
        if values.get("LLM_ALLOW_EXTERNAL_API", "false") != "true":
            raise LLMConfigurationError("La API externa está desactivada: falta LLM_ALLOW_EXTERNAL_API=true.")
        raw_budget = str(max_output_tokens) if max_output_tokens is not None else values.get("UNAB_MAX_OUTPUT_TOKENS", "2048")
        try:
            budget = int(raw_budget) if isinstance(raw_budget, str) else None
        except ValueError:
            budget = None
        if budget is None or not 16 <= budget <= 4096:
            raise LLMConfigurationError("UNAB_MAX_OUTPUT_TOKENS debe ser un entero entre 16 y 4096.")
        return UNABClient(UNABSettings(model=model if model is not None else values.get("UNAB_MODEL", "gemma4:26b"), max_output_tokens=budget, **overrides),
                          api_key=values.get("UNAB_API_KEY", ""), transport=transport)
    if provider != "openai":
        raise LLMConfigurationError("LLM_PROVIDER debe ser ollama, unab u openai.")
    if values.get("LLM_ALLOW_EXTERNAL_API", "false") != "true":
        raise LLMConfigurationError("La API externa está desactivada: falta LLM_ALLOW_EXTERNAL_API=true.")
    settings = OpenAISettings(
        model=model if model is not None else values.get("OPENAI_MODEL", ""),
        max_output_tokens=max_output_tokens if max_output_tokens is not None else 512,
        **overrides,
    )
    return OpenAIClient(settings, api_key=values.get("OPENAI_API_KEY", ""), transport=transport)

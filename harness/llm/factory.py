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
) -> OllamaClient | OpenAIClient | UNABClient:
    """Crear sin enviar solicitudes; no lee archivos .env ni cambia al fallar."""

    values = os.environ if environ is None else environ
    provider = values.get("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        try:
            settings = OllamaSettings(model=values.get("OLLAMA_MODEL", OllamaSettings().model))
        except ValueError as error:
            raise LLMConfigurationError(f"OLLAMA_MODEL inválido: {error}") from error
        return OllamaClient(settings, transport=transport)
    if provider == "unab":
        if values.get("LLM_ALLOW_EXTERNAL_API", "false") != "true":
            raise LLMConfigurationError("La API externa está desactivada: falta LLM_ALLOW_EXTERNAL_API=true.")
        raw_budget = values.get("UNAB_MAX_OUTPUT_TOKENS", "2048")
        try:
            budget = int(raw_budget) if isinstance(raw_budget, str) else None
        except ValueError:
            budget = None
        if budget is None or not 16 <= budget <= 4096:
            raise LLMConfigurationError("UNAB_MAX_OUTPUT_TOKENS debe ser un entero entre 16 y 4096.")
        return UNABClient(UNABSettings(model=values.get("UNAB_MODEL", "gemma4:26b"), max_output_tokens=budget),
                          api_key=values.get("UNAB_API_KEY", ""), transport=transport)
    if provider != "openai":
        raise LLMConfigurationError("LLM_PROVIDER debe ser ollama, unab u openai.")
    if values.get("LLM_ALLOW_EXTERNAL_API", "false") != "true":
        raise LLMConfigurationError("La API externa está desactivada: falta LLM_ALLOW_EXTERNAL_API=true.")
    settings = OpenAISettings(model=values.get("OPENAI_MODEL", ""))
    return OpenAIClient(settings, api_key=values.get("OPENAI_API_KEY", ""), transport=transport)

"""Parámetros sin secretos para los adaptadores local y externo."""

from dataclasses import dataclass
from math import isfinite
from re import fullmatch
from urllib.parse import urlsplit


class LLMConfigurationError(ValueError):
    """Selección o parámetros incompletos, antes de hacer solicitudes."""


@dataclass(frozen=True, slots=True)
class OllamaSettings:
    """Sin lectura de .env ni selección automática de otro proveedor."""

    base_url: str = "http://127.0.0.1:11434"
    model: str = "gemma3n:e2b"
    read_timeout_seconds: float = 300.0
    connect_timeout_seconds: float = 5.0
    context_size: int = 8192
    max_output_tokens: int = 512
    temperature: float = 0.2
    connection_retries: int = 1
    keep_alive: str = "15m"

    def __post_init__(self) -> None:
        if not isinstance(self.base_url, str):
            raise ValueError("base_url debe ser una dirección local de Ollama.")
        try:
            url = urlsplit(self.base_url)
            port = url.port
        except ValueError as exc:
            raise ValueError("base_url no es una dirección válida.") from exc
        if (
            url.scheme != "http"
            or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or port is None
            or url.username is not None
            or url.password is not None
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
        ):
            raise ValueError("base_url debe usar HTTP, un puerto y una dirección de este equipo.")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model debe identificar un modelo local instalado.")
        if self.model != self.model.strip() or self.model.lower().endswith((":cloud", "-cloud")):
            raise ValueError("Esta configuración solo admite modelos locales, sin espacios externos.")
        for field in ("read_timeout_seconds", "connect_timeout_seconds"):
            value = getattr(self, field)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError(f"{field} debe ser un número finito mayor que cero.")
        for field in ("context_size", "max_output_tokens"):
            value = getattr(self, field)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field} debe ser un entero mayor que cero.")
        if self.max_output_tokens >= self.context_size:
            raise ValueError("max_output_tokens debe ser menor que context_size.")
        if (
            type(self.temperature) not in (int, float)
            or not isfinite(self.temperature)
            or not 0 <= self.temperature <= 2
        ):
            raise ValueError("temperature debe ser un número finito entre 0 y 2.")
        if type(self.connection_retries) is not int or not 0 <= self.connection_retries <= 2:
            raise ValueError("connection_retries debe ser un entero entre 0 y 2.")
        if not isinstance(self.keep_alive, str) or fullmatch(r"(?:0|[1-9][0-9]*[smh])", self.keep_alive) is None:
            raise ValueError("keep_alive debe ser 0 o una duración positiva como 30s, 5m o 1h.")


@dataclass(frozen=True, slots=True)
class OpenAISettings:
    """El modelo se elige explícitamente; las credenciales no forman parte del objeto."""

    model: str
    read_timeout_seconds: float = 90.0
    connect_timeout_seconds: float = 5.0
    max_output_tokens: int = 512
    connection_retries: int = 1

    def __post_init__(self) -> None:
        if (
            not isinstance(self.model, str)
            or not self.model
            or any(character.isspace() for character in self.model)
        ):
            raise LLMConfigurationError("OPENAI_MODEL debe identificar un modelo compatible con Responses.")
        for field in ("read_timeout_seconds", "connect_timeout_seconds"):
            value = getattr(self, field)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise LLMConfigurationError(f"{field} debe ser un número finito mayor que cero.")
        if type(self.max_output_tokens) is not int or self.max_output_tokens < 16:
            raise LLMConfigurationError("max_output_tokens debe ser un entero de al menos 16.")
        if type(self.connection_retries) is not int or not 0 <= self.connection_retries <= 2:
            raise LLMConfigurationError("connection_retries debe ser un entero entre 0 y 2.")

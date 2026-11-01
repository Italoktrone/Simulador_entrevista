"""Contrato de respuesta y errores compartidos, independiente del proveedor."""

from dataclasses import dataclass
from typing import Protocol

from harness.llm.messages import ChatMessage


class LLMError(RuntimeError):
    """Error conocido al solicitar una respuesta del modelo."""


class LLMConnectionError(LLMError):
    """No se pudo establecer la conexión con el servicio."""


class LLMAuthenticationError(LLMError):
    """El proveedor rechazó las credenciales o permisos de acceso."""


class LLMTimeoutError(LLMError):
    """Se agotó un tiempo de espera de la solicitud."""


class LLMModelNotFoundError(LLMError):
    """El modelo solicitado no está disponible."""


class LLMProviderError(LLMError):
    """El servicio rechazó la solicitud o falló al procesarla."""


class LLMContextLimitError(LLMError):
    """El proveedor rechazó una solicitud por falta de espacio de contexto."""


class LLMInvalidResponseError(LLMError):
    """El servicio devolvió una respuesta incompleta o de formato inesperado."""


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    elapsed_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None
    server_total_seconds: float | None = None
    load_seconds: float | None = None
    prompt_eval_seconds: float | None = None
    eval_seconds: float | None = None
    cached_input_tokens: int | None = None


class LLMClient(Protocol):
    """Interfaz compartida por el adaptador local y el externo."""

    def generate(self, messages: list[ChatMessage]) -> LLMResponse: ...

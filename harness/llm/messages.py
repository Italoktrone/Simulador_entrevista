"""Contrato sencillo de mensajes, independiente del proveedor del LLM."""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """Diccionario serializable que un adaptador enviará al proveedor."""

    role: Literal["system", "user", "assistant"]
    content: str


def validate_messages(messages: list[ChatMessage]) -> None:
    """Comprobar el contrato antes de hacer una solicitud HTTP, sin volcar su contenido."""

    if not isinstance(messages, list) or not messages:
        raise ValueError("Se necesita una lista no vacía de mensajes.")
    for index, message in enumerate(messages):
        if not isinstance(message, dict) or set(message) != {"role", "content"}:
            raise ValueError(f"El mensaje {index} debe contener únicamente role y content.")
        if not isinstance(message["role"], str) or message["role"] not in {"system", "user", "assistant"}:
            raise ValueError(f"El mensaje {index} tiene un rol no admitido.")
        if not isinstance(message["content"], str) or not message["content"].strip():
            raise ValueError(f"El mensaje {index} debe tener contenido de texto no vacío.")

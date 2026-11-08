"""Diagnóstico mínimo: nunca serializa instancias, esquemas o excepciones crudas."""

from dataclasses import dataclass
import re

from harness.classification_contract import classification_expectation_schema


@dataclass(frozen=True, slots=True)
class ValidationAudit:
    path: str
    rule: str
    message: str


def _redact(text: str) -> str:
    # Defensa adicional; los validadores solo producen explicaciones del programa.
    text = re.sub(r"-----BEGIN[^\r\n]*PRIVATE KEY-----.*?-----END[^\r\n]*PRIVATE KEY-----",
                  "[REDACTED]", text, flags=re.S)
    text = re.sub(r"(?i)\b(?:bearer|basic)\s+[^\s,;]+", "[REDACTED]", text)
    text = re.sub(r"(?i)\b(?:api[_-]?key|token|password|secret|authorization|clave)\b"
                  r"[\s\"']*[:=][\s\"']*[^\s,;]+", "[REDACTED]", text)
    text = re.sub(r"\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]+", "[REDACTED]", text)
    return " ".join(text.split())[:1000]


def safe_validation_audit(error) -> ValidationAudit:
    """Ruta restringida a nombres del contrato e índices; sin valores rechazados.

    detail procede de mensajes controlados de DataValidationError, nunca de
    jsonschema.ValidationError.message, que puede incluir el valor sensible.
    """
    allowed = {"quote"}
    def collect(node):
        if isinstance(node, dict):
            allowed.update(node.get("properties", {}))
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)
    collect(classification_expectation_schema())
    parts = error.path.split("/")
    path = "/".join(part if part in allowed or part.isascii() and part.isdigit() or not part
                    else "[REDACTED]" for part in parts)
    if error.path == "raíz":
        path = "/"
    return ValidationAudit(path, _redact(error.rule), _redact(error.detail))

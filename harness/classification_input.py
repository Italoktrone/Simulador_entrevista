"""Validación compartida de la entrada del clasificador, sin interpretar texto."""

import json
from pathlib import Path
import re

from harness.json_loader import load_json
from harness.schema_validator import validate_data


CONFIG_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/interview_config.schema.json"


def validate_classification_input(intervention_id, text, configuration, context_turns, competency) -> tuple[int, ...]:
    """Devolver los turnos autorizados del fragmento aportado por el llamador.

    No lee sesiones ni el perfil. El llamador selecciona contexto pertinente
    de su sesión; aquí solo se comprueba forma, roles, orden y límites.
    """
    try:
        json.dumps([text, configuration, context_turns, competency], ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ValueError("La entrada debe contener datos JSON UTF-8 válidos.") from None
    if not isinstance(intervention_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}", intervention_id) is None:
        raise ValueError("El identificador de intervención no tiene un formato válido.")
    if not isinstance(text, str):
        raise ValueError("La intervención debe contener texto.")
    if competency is not None and (not isinstance(competency, str) or not competency.strip()):
        raise ValueError("La competencia debe ser texto no vacío o None.")
    if configuration is not None:
        validate_data(configuration, load_json(CONFIG_SCHEMA_PATH))
    if not isinstance(context_turns, (list, tuple)):
        raise ValueError("El contexto debe ser una secuencia de turnos de la misma sesión.")
    ids = []
    for turn in context_turns:
        if not isinstance(turn, dict) or set(turn) != {"turn_number", "messages"}:
            raise ValueError("Cada turno de contexto necesita número y mensajes.")
        number = turn["turn_number"]
        if type(number) is not int or number < 1 or (configuration is not None and number >= configuration["max_questions"]):
            raise ValueError("Número de turno de contexto no permitido.")
        messages = turn["messages"]
        if not isinstance(messages, list) or not messages:
            raise ValueError("Cada turno de contexto necesita mensajes no vacíos.")
        for message in messages:
            if (not isinstance(message, dict) or set(message) != {"role", "content"}
                    or message["role"] not in ("user", "assistant")
                    or not isinstance(message["content"], str) or not message["content"].strip()):
                raise ValueError("El contexto solo admite mensajes de entrevistador o candidato, sin instrucciones system.")
        ids.append(number)
    if ids != sorted(set(ids)):
        raise ValueError("Los turnos de contexto deben ser únicos y estar ordenados.")
    return tuple(ids)

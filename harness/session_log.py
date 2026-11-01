"""Guardado y lectura de sesiones cerradas en JSON local, sin reanudarlas."""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
from uuid import UUID

from harness.json_loader import load_json
from harness.schema_validator import validate_data
from harness.live_context import validate_live_context_log


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSIONS_DIR = PROJECT_ROOT / "outputs/sessions"
SESSION_SCHEMA_PATH = PROJECT_ROOT / "schemas/session.schema.json"
CONFIG_SCHEMA_PATH = PROJECT_ROOT / "schemas/interview_config.schema.json"


class SessionLogError(RuntimeError):
    """No se puede validar, guardar o leer un registro de sesión."""


def _encode(data: object) -> bytes:
    try:
        return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise SessionLogError("El registro contiene valores que no se pueden guardar como JSON UTF-8.") from None


def _check_utc(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value) or parsed.utcoffset() != timedelta(0):
            raise ValueError
    except ValueError:
        raise SessionLogError(f"La fecha de {field} debe ser válida e indicar UTC.") from None


def validate_session_data(data: object, schema: dict, config_schema: dict) -> None:
    """Validar forma y relaciones del archivo sin I/O ni cambios de los datos.

    La configuración reutiliza su propio esquema. Las fechas se comprueban
    como UTC reales; el orden de los intentos lo fija question_number, sin
    imponer monotonía al reloj del sistema o a comprobaciones tras el cierre.
    """
    _encode(data)
    try:
        validate_data(data, schema)
        validate_data(data["configuration"], config_schema)
    except ValueError:
        raise SessionLogError("El registro o su configuración no cumplen los esquemas de sesión.") from None
    config = data["configuration"]
    try:
        identifier = UUID(data["session_id"])
    except ValueError:
        raise SessionLogError("El identificador de sesión no es un UUID válido.") from None
    if identifier.version != 4 or str(identifier) != data["session_id"]:
        raise SessionLogError("El identificador de sesión debe ser un UUID canónico de versión 4.")
    if data["candidate_id"] != config["candidate_id"] or data["job_id"] != config["job_id"]:
        raise SessionLogError("Las referencias de candidato o puesto no coinciden con la configuración.")
    attempts = data["attempts"]
    if len(attempts) > config["max_questions"]:
        raise SessionLogError("El registro supera el límite de preguntas configurado.")
    if data["close_reason"] == "question_limit" and len(attempts) != config["max_questions"]:
        raise SessionLogError("El cierre por límite no coincide con las preguntas registradas.")
    _check_utc(data["created_at"], "created_at")
    _check_utc(data["closed_at"], "closed_at")
    integrity_issue = False
    for issue in data["issues"]:
        _check_utc(issue["recorded_at"], "issues.recorded_at")
        integrity_issue |= issue["code"] == "profile_integrity_error"
    for event in data.get("context_events", []):
        _check_utc(event["recorded_at"], "context_events.recorded_at")
        integrity_issue |= any(issue["code"] == "profile_integrity_error" for issue in event["issues"])
    for number, attempt in enumerate(attempts, 1):
        if attempt["question_number"] != number:
            raise SessionLogError("Los intentos deben estar numerados consecutivamente desde uno.")
        _check_utc(attempt["requested_at"], "attempts.requested_at")
        _check_utc(attempt["finished_at"], "attempts.finished_at")
        response = attempt["response"]
        status = attempt["status"]
        if status == "completed":
            if response is None or response["finish_reason"] == "length" or attempt["issues"]:
                raise SessionLogError("Un intento completo necesita una respuesta aceptada y no puede tener incidencias.")
        elif not attempt["issues"]:
            raise SessionLogError("Un intento fallido o interrumpido necesita una incidencia técnica.")
        if status == "incomplete" and (response is None or response["finish_reason"] != "length"):
            raise SessionLogError("Un intento incompleto debe conservar su respuesta cortada para diagnóstico.")
        integrity_issue |= any(issue["code"] == "profile_integrity_error" for issue in attempt["issues"])
    if integrity_issue and data["source_integrity"] != "failed":
        raise SessionLogError("La incidencia de integridad no coincide con el estado del perfil registrado.")
    try:
        validate_live_context_log(data)
    except ValueError:
        raise SessionLogError("La auditoría de contexto no coincide con la política o el historial registrado.") from None


def _validate(data: object) -> None:
    try:
        schema = load_json(SESSION_SCHEMA_PATH)
        config_schema = load_json(CONFIG_SCHEMA_PATH)
    except ValueError:
        raise SessionLogError("No se pudieron cargar los esquemas locales de sesión y configuración.") from None
    validate_session_data(data, schema, config_schema)


def save_session(data: dict, directory: str | Path | None = None) -> Path:
    """Crear una sola vez el archivo de una sesión cerrada; nunca sobrescribir.

    Valida y codifica antes de crear el directorio. Una escritura fallida
    elimina únicamente el archivo que esta llamada llegó a crear.
    """
    _validate(data)
    encoded = _encode(data)
    directory = DEFAULT_SESSIONS_DIR if directory is None else Path(directory)
    try:
        output = directory.resolve() / f"session-{data['session_id']}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise SessionLogError(f"No se pudo preparar la carpeta de sesiones: {directory}") from None
    try:
        stream = output.open("xb")
    except FileExistsError:
        raise SessionLogError(f"El archivo ya existe y no se sobrescribió: {output}") from None
    except OSError:
        raise SessionLogError(f"No se pudo crear el archivo de sesión: {output}") from None
    try:
        with stream:
            if stream.write(encoded) != len(encoded):
                raise OSError("Escritura incompleta")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException as error:
        try:
            output.unlink()
        except OSError:
            raise SessionLogError(f"No se completó el guardado y debe revisarse el archivo posiblemente incompleto: {output}") from None
        if isinstance(error, OSError):
            raise SessionLogError(f"No se pudo guardar la sesión; revisa la carpeta, sus permisos y el espacio disponible: {output}") from None
        raise
    return output


def load_session(path: str | Path) -> dict:
    """Leer y validar datos; no ejecuta contenido ni reabre la conversación."""
    try:
        data = load_json(path)
    except ValueError:
        raise SessionLogError("No se pudo leer un archivo de sesión JSON válido; comprueba ruta, contenido y permisos.") from None
    _validate(data)
    return data

"""Lectura de JSON local en UTF-8, sin modificar archivos ni validar esquemas."""

import json
import math
from pathlib import Path
from typing import Any, NoReturn


class JsonLoadError(ValueError):
    """No se pudo leer o interpretar un archivo JSON."""

    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        super().__init__(f"No se pudo cargar '{path}': {detail}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Evita que una clave repetida sobrescriba silenciosamente su valor."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Clave JSON repetida: {key!r}.")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f"La constante {value} no está permitida en JSON.")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Un número decimal supera el rango finito admitido.")
    return number


def load_json(path: str | Path) -> Any:
    """Lee JSON en UTF-8 con o sin BOM y devuelve un valor de Python.

    Rechaza claves repetidas, constantes no admitidas y números decimales que
    desborden a infinito. Los errores de lectura o formato se comunican como
    JsonLoadError. La estructura y coherencia se validan en otros módulos.
    Cada llamada realiza una lectura independiente, sin guardar una caché.
    """
    data, _ = load_json_with_bytes(path)
    return data


def load_json_with_bytes(path: str | Path) -> tuple[Any, bytes]:
    """Devuelve datos y bytes originales procedentes de una misma lectura.

    Permite calcular una huella sobre exactamente el contenido interpretado,
    conservando BOM, saltos de línea y demás detalles del archivo original.
    """
    file_path = Path(path)
    try:
        raw_bytes = file_path.read_bytes()
        text = raw_bytes.decode("utf-8-sig")
    except FileNotFoundError as error:
        raise JsonLoadError(file_path, "El archivo no existe.") from error
    except UnicodeDecodeError as error:
        raise JsonLoadError(file_path, "El archivo no tiene codificación UTF-8 válida.") from error
    except OSError as error:
        raise JsonLoadError(
            file_path, "No se puede leer como archivo; comprueba la ruta y los permisos."
        ) from error

    try:
        data = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
        return data, raw_bytes
    except json.JSONDecodeError as error:
        raise JsonLoadError(
            file_path,
            f"JSON inválido en la línea {error.lineno}, columna {error.colno}.",
        ) from error
    except ValueError as error:
        raise JsonLoadError(file_path, str(error)) from error
    except RecursionError as error:
        raise JsonLoadError(
            file_path, "El documento tiene demasiados niveles de anidación."
        ) from error

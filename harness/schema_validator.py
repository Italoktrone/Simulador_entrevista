"""Validación estructural con JSON Schema 2020-12, sin lectura de archivos.

Las relaciones entre registros, el calendario y la cronología se comprobarán
en los módulos de datos. Esta función no completa ni modifica antecedentes.
"""

from collections.abc import Iterable
from typing import Any

from jsonschema import Draft202012Validator, SchemaError, ValidationError


class InvalidSchemaError(ValueError):
    """El esquema contiene una regla inválida y debe corregirse."""


class DataValidationError(ValueError):
    """Los datos incumplen una regla del esquema."""

    def __init__(self, path: str, rule: str, detail: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"Datos inválidos en {path}: {detail}")


def _format_path(parts: Iterable[str | int]) -> str:
    """Indica la raíz o una ruta JSON Pointer, incluidos índices de listas."""
    escaped = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped) if escaped else "raíz"


def _describe_error(error: ValidationError) -> str:
    """Explica la regla sin incluir el valor rechazado ni el perfil completo."""
    if error.validator == "required":
        missing = [name for name in error.validator_value if name not in error.instance]
        return f"Faltan campos obligatorios: {', '.join(missing)}."

    messages = {
        "type": "El tipo de dato no coincide con el esquema.",
        "const": "El valor no coincide con el definido en el esquema.",
        "enum": "El valor no está entre las opciones permitidas.",
        "pattern": "El texto no tiene el formato esperado.",
        "minLength": "El texto tiene menos caracteres de los requeridos.",
        "minItems": "La lista tiene menos elementos de los requeridos.",
        "uniqueItems": "La lista contiene elementos repetidos.",
        "minimum": "El número es menor que el mínimo permitido.",
        "maximum": "El número supera el máximo permitido.",
        "additionalProperties": "Hay campos que el esquema no permite.",
        "not": "Los datos contienen una combinación no permitida.",
        "anyOf": "No se cumple ninguna de las alternativas requeridas.",
        "oneOf": "Debe cumplirse exactamente una de las alternativas requeridas.",
    }
    return messages.get(error.validator, "No se cumple una regla del esquema.")


def validate_data(data: object, schema: dict[str, Any]) -> None:
    """Valida datos ya cargados y devuelve None si cumplen el esquema.

    Lanza InvalidSchemaError si las reglas están mal definidas, o
    DataValidationError ante el primer error de datos. Esta última excepción
    expone path y rule para que la interfaz pueda mostrar un error comprensible.
    No valida calendario, cronología, existencia de referencias ni unicidad
    de identificadores entre registros distintos.
    """
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        path = _format_path(error.absolute_path)
        raise InvalidSchemaError(
            f"El esquema contiene una regla incorrecta en {path}."
        ) from error

    try:
        Draft202012Validator(schema).validate(data)
    except ValidationError as error:
        raise DataValidationError(
            path=_format_path(error.absolute_path),
            rule=str(error.validator),
            detail=_describe_error(error),
        ) from error

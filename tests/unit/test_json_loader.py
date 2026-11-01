"""Pruebas de lectura, interpretación estricta e independencia de los JSON."""

import json
from pathlib import Path

import pytest

from harness.json_loader import JsonLoadError, load_json, load_json_with_bytes


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_reads_unicode_with_or_without_bom_without_modifying_file(tmp_path, encoding):
    path = tmp_path / "perfil.json"
    expected = {"name": "Nicolás Vera Soto", "description": "Formación y colaboración"}
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding=encoding)
    before = path.read_bytes()

    assert load_json(path) == expected
    assert path.read_bytes() == before


@pytest.mark.parametrize("value", [None, True, 123, 1.5, "texto", [], {"x": 1}])
def test_reads_json_root_types_without_enforcing_a_schema(tmp_path, value):
    path = tmp_path / "datos.json"
    path.write_text(json.dumps(value), encoding="utf-8")

    assert load_json(path) == value


def test_reports_missing_file(tmp_path):
    path = tmp_path / "ausente.json"

    with pytest.raises(JsonLoadError, match="El archivo no existe") as caught:
        load_json(path)

    assert caught.value.path == path
    assert not path.exists()


def test_reports_permission_error(tmp_path, monkeypatch):
    def deny_read(self, **kwargs):
        raise PermissionError("Permiso denegado de prueba")

    monkeypatch.setattr(Path, "read_bytes", deny_read)

    with pytest.raises(JsonLoadError, match="permisos"):
        load_json(tmp_path / "perfil.json")


def test_reports_other_read_errors(tmp_path, monkeypatch):
    def fail_read(self, **kwargs):
        raise OSError("Error de dispositivo de prueba")

    monkeypatch.setattr(Path, "read_bytes", fail_read)

    with pytest.raises(JsonLoadError, match="No se puede leer"):
        load_json(tmp_path / "perfil.json")


def test_reports_directory_instead_of_file(tmp_path):
    with pytest.raises(JsonLoadError, match="No se puede leer"):
        load_json(tmp_path)


@pytest.mark.parametrize("encoding", ["utf-16", "cp1252"])
def test_rejects_non_utf8_encoding(tmp_path, encoding):
    path = tmp_path / "perfil.json"
    path.write_bytes('{"name": "Nicolás"}'.encode(encoding))

    with pytest.raises(JsonLoadError, match="UTF-8"):
        load_json(path)


@pytest.mark.parametrize("text", ["", "{'name': 'x'}", '{"name":}', '{"name":"x",}', "{"])
def test_reports_invalid_json_with_line_and_column(tmp_path, text):
    path = tmp_path / "invalido.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(JsonLoadError, match=r"línea [0-9]+, columna [0-9]+"):
        load_json(path)


@pytest.mark.parametrize(
    "text",
    [
        '{"name":"Primero","name":"Segundo"}',
        '{"project":{"id":"proj-001","id":"proj-002"}}',
    ],
    ids=["root-key", "nested-key"],
)
def test_rejects_duplicate_keys(tmp_path, text):
    path = tmp_path / "duplicado.json"
    path.write_text(text, encoding="utf-8")
    before = path.read_bytes()

    with pytest.raises(JsonLoadError, match="Clave JSON repetida"):
        load_json(path)

    assert path.read_bytes() == before


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_rejects_non_json_numeric_constants(tmp_path, constant):
    path = tmp_path / "numero.json"
    path.write_text('{"value":' + constant + "}", encoding="utf-8")

    with pytest.raises(JsonLoadError, match="no está permitida"):
        load_json(path)


@pytest.mark.parametrize("number", ["1e400", "-1e400"])
def test_rejects_decimal_overflow(tmp_path, number):
    path = tmp_path / "desbordamiento.json"
    path.write_text(number, encoding="utf-8")

    with pytest.raises(JsonLoadError, match="rango finito"):
        load_json(path)


def test_reports_decoder_recursion_errors(tmp_path, monkeypatch):
    path = tmp_path / "profundo.json"
    path.write_text("{}", encoding="utf-8")

    def fail_decode(*args, **kwargs):
        raise RecursionError("Límite del decodificador simulado")

    monkeypatch.setattr("harness.json_loader.json.loads", fail_decode)

    with pytest.raises(JsonLoadError, match="niveles de anidación"):
        load_json(path)


def test_each_read_has_independent_data(tmp_path):
    path = tmp_path / "perfil.json"
    path.write_text('{"tools":["Python"]}', encoding="utf-8")
    first = load_json(path)
    second = load_json(path)

    first["tools"].append("Dato solo en memoria")

    assert second == {"tools": ["Python"]}
    assert load_json(path) == {"tools": ["Python"]}


def test_accepts_string_path(tmp_path):
    path = tmp_path / "perfil.json"
    path.write_text('{"candidate_id":"cand-001"}', encoding="utf-8")

    assert load_json(str(path)) == {"candidate_id": "cand-001"}


def test_preserves_exact_bytes_with_bom_and_windows_newlines(tmp_path):
    path = tmp_path / "perfil.json"
    original = b'\xef\xbb\xbf{\r\n  "candidate_id": "cand-001"\r\n}\r\n'
    path.write_bytes(original)

    data, raw_bytes = load_json_with_bytes(path)

    assert data == {"candidate_id": "cand-001"}
    assert raw_bytes == original
    assert path.read_bytes() == original


def test_data_and_original_bytes_come_from_one_read(tmp_path, monkeypatch):
    path = tmp_path / "perfil.json"
    first = b'{"candidate_id":"cand-001"}'
    other = b'{"candidate_id":"cand-002"}'
    reads = []

    def changing_read(self):
        reads.append(self)
        return first if len(reads) == 1 else other

    monkeypatch.setattr(Path, "read_bytes", changing_read)

    data, raw_bytes = load_json_with_bytes(path)

    assert reads == [path]
    assert data == {"candidate_id": "cand-001"}
    assert raw_bytes == first

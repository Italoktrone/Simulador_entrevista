"""Fuentes reales → casos resueltos → presentación, sin red o archivos nuevos."""

from pathlib import Path

import httpx
import pytest

from harness.reference_cases import DEFAULT_SCHEMA_PATH, DEFAULT_SUITE_PATH, load_reference_suite
from scripts import show_reference_cases


def test_listing_resolves_real_facts_without_network_or_changes(monkeypatch, capsys, tmp_path):
    root = Path(__file__).resolve().parents[2]
    sources = [DEFAULT_SUITE_PATH, DEFAULT_SCHEMA_PATH, *[root / p for p in (
        "data/candidates/candidato_junior.json", "data/jobs/desarrollador_junior.json",
        "config/interviews/basica.json", "agent/agent.md",
    )]]
    before = {path: path.read_bytes() for path in sources}
    sessions = {p: p.read_bytes() for p in (root / "outputs/sessions").glob("session-*.json")}

    def no_network(*args, **kwargs):
        pytest.fail("Preparar casos no debe consultar a un proveedor")

    monkeypatch.setattr(httpx.Client, "send", no_network)
    monkeypatch.chdir(tmp_path)
    assert show_reference_cases.main([]) == 0
    output = capsys.readouterr().out
    assert "Casos: 4. Entradas de pregunta: 5." in output
    assert "Instituto Profesional Horizonte Digital" in output and "Ingeniería en Informática" in output
    assert "Meses calendario distintos (contenido esperado): 21" in output
    assert "Meses de práctica (contenido esperado): 3" in output
    assert "Meses posteriores como junior (contenido esperado): 18" in output
    assert "Inventario Aula" in output and "Sin experiencia práctica con Kubernetes." in output
    assert "Ejecuciones y revisión de respuestas pendientes" in output
    assert {p: p.read_bytes() for p in sources} == before
    assert {p: p.read_bytes() for p in (root / "outputs/sessions").glob("session-*.json")} == sessions
    assert list(tmp_path.iterdir()) == []


def test_failed_listing_does_not_print_criteria_or_create_files(tmp_path, capsys):
    assert show_reference_cases.main(["--suite", str(tmp_path / "missing.json")]) == 1
    output = capsys.readouterr().out
    assert "No se pudieron preparar los casos" in output and "Casos: 4" not in output
    assert list(tmp_path.iterdir()) == []


def test_repeated_loading_has_separate_case_views():
    first, second = load_reference_suite(), load_reference_suite()
    assert first.source_sha256 == second.source_sha256
    modified = first.resolved_cases()
    modified[2]["steps"][1]["question"] = "Cambio local"
    assert "Cambio local" not in str(second.resolved_cases())

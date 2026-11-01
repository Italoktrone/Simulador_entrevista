"""Vista pública derivada del perfil y presentación sin antecedentes internos."""

import json
from pathlib import Path

import pytest

from harness.application.cli import format_resume
from harness.json_loader import load_json
from harness.profile import load_profile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "data/candidates/candidato_junior.json"


def test_public_resume_uses_professional_data_from_single_source():
    profile = load_profile(SOURCE_PATH)
    source = profile.to_dict()

    resume = profile.to_public_resume()

    assert resume["candidate_id"] == source["candidate_id"]
    assert resume["name"] == source["name"]
    assert resume["professional_summary"] == source["professional_summary"]
    assert resume["education"][0]["graduation_month"] == "2025-12"
    role = resume["work_experience"][0]["roles"][1]
    assert (role["start_month"], role["end_month"]) == ("2025-04", "2026-09")
    assert [period["schedule"] for period in role["schedule_periods"]] == [
        "Jornada parcial", "Jornada completa",
    ]
    assert [item["name"] for item in resume["projects"]] == ["MesaFaro", "Inventario Aula"]


def test_public_resume_has_only_authorized_fields_at_every_level():
    resume = load_profile(SOURCE_PATH).to_public_resume()

    assert set(resume) == {
        "candidate_id", "name", "professional_summary", "education",
        "work_experience", "technical_skills", "tools_used", "projects",
    }
    for record in resume["education"]:
        assert set(record) == {
            "institution", "degree", "start_month", "end_month", "graduation_month", "status",
        }
    for employer in resume["work_experience"]:
        assert set(employer) == {"organization", "roles"}
        for role in employer["roles"]:
            assert set(role) == {
                "title", "start_month", "end_month", "responsibilities", "schedule_periods",
            }
            for period in role["schedule_periods"]:
                assert set(period) == {"start_month", "end_month", "schedule"}
    for project in resume["projects"]:
        assert set(project) == {
            "name", "kind", "description", "start_month", "end_month",
            "technologies_used", "personal_contributions",
        }


@pytest.mark.parametrize(
    "keys",
    [
        ("behavioral_situations", 0, "context"),
        ("achievements", 0, "scenario_evidence"),
        ("improvement_areas", 0, "description"),
        ("strengths", 0, "description"),
        ("professional_competencies", 0, "name"),
        ("work_motivation",),
        ("personality", "interview_behavior", 0),
        ("technical_knowledge", 3, "scope"),
        ("work_experience", 0, "team_context"),
        ("work_experience", 0, "authority_limits", 0),
        ("projects", 0, "contribution_limits", 0),
        ("professional_status", "reason_last_contract_ended"),
    ],
)
def test_internal_text_does_not_leak_to_resume_or_console(tmp_path, keys):
    data = load_json(SOURCE_PATH)
    node = data
    for key in keys[:-1]:
        node = node[key]
    marker = "CONTENIDO_INTERNO_NO_PUBLICAR"
    node[keys[-1]] = marker
    path = tmp_path / "perfil.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    profile = load_profile(path)

    assert marker not in json.dumps(profile.to_public_resume(), ensure_ascii=False)
    assert marker not in format_resume(profile)


def test_modifying_public_copy_cannot_change_snapshot_or_other_copies():
    profile = load_profile(SOURCE_PATH)
    original = profile.to_dict()
    expected = profile.to_public_resume()
    changed = profile.to_public_resume()

    changed["education"][0]["degree"] = "Dato solo de una copia"
    changed["work_experience"][0]["roles"][0]["responsibilities"].append("Otra tarea")
    changed["projects"][0]["technologies_used"].append("Otra tecnología")

    assert profile.to_public_resume() == expected
    assert profile.to_dict() == original
    assert profile.assert_source_unchanged() is None


def test_fresh_resume_reflects_source_without_a_separate_cv_file(tmp_path):
    data = load_json(SOURCE_PATH)
    data["name"] = "Nombre actualizado de prueba"
    path = tmp_path / "perfil.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    profile = load_profile(path)

    assert profile.to_public_resume()["name"] == "Nombre actualizado de prueba"
    assert "Nombre actualizado de prueba" in format_resume(profile)


def test_merges_role_responsibilities_without_repeated_items(tmp_path):
    data = load_json(SOURCE_PATH)
    periods = data["work_experience"][0]["roles"][1]["schedule_periods"]
    repeated = periods[1]["responsibilities"][0]
    periods[0]["responsibilities"].append(repeated)
    path = tmp_path / "perfil.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    resume = load_profile(path).to_public_resume()

    assert resume["work_experience"][0]["roles"][1]["responsibilities"].count(repeated) == 1


def test_console_shows_readable_professional_sections_and_dates():
    profile = load_profile(SOURCE_PATH)

    text = format_resume(profile)

    for expected in (
        "CURRÍCULUM RESUMIDO", "Nicolás Vera Soto", "FORMACIÓN", "EXPERIENCIA LABORAL",
        "CONOCIMIENTOS TÉCNICOS", "HERRAMIENTAS", "PROYECTOS",
        "Titulación: diciembre de 2025", "abril de 2025 a septiembre de 2026",
        "Jornada parcial: abril de 2025 a diciembre de 2025",
        "Jornada completa: enero de 2026 a septiembre de 2026",
        "MesaFaro", "Inventario Aula",
    ):
        assert expected in text
    assert "candidate_id" not in text
    assert profile.source_sha256 not in text
    assert str(profile.source_path) not in text


def test_resume_projection_and_formatting_do_not_access_files(monkeypatch):
    profile = load_profile(SOURCE_PATH)

    def deny_read(self):
        raise AssertionError("La vista debe utilizar la instantánea en memoria")

    monkeypatch.setattr(Path, "read_bytes", deny_read)

    assert profile.to_public_resume()["candidate_id"] == "cand-001"
    assert "Nicolás Vera Soto" in format_resume(profile)

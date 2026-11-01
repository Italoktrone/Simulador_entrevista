"""Preparación de la configuración, candidato y puesto reales aprobados."""

import hashlib
from pathlib import Path

from harness.interview_config import load_interview_setup


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_prepares_initial_scenario_and_keeps_all_source_files_unchanged():
    paths = [
        PROJECT_ROOT / "config/interviews/basica.json",
        PROJECT_ROOT / "data/candidates/candidato_junior.json",
        PROJECT_ROOT / "data/jobs/desarrollador_junior.json",
    ]
    before = [path.read_bytes() for path in paths]

    setup = load_interview_setup()

    assert setup.config_dict()["config_id"] == "entrevista-basica-001"
    assert setup.config_dict()["candidate_id"] == setup.candidate.candidate_id
    assert setup.config_dict()["job_id"] == setup.job_dict()["job_id"]
    assert setup.candidate.to_dict()["target_job_id"] == setup.job_dict()["job_id"]
    assert setup.job_dict()["competencies_to_explore"] == [
        "Resolución de problemas", "Comunicación", "Colaboración",
        "Organización", "Aprendizaje", "Responsabilidad",
    ]
    assert setup.candidate.assert_source_unchanged() is None
    assert [path.read_bytes() for path in paths] == before
    assert hashlib.sha256(before[1]).hexdigest().upper() == (
        "6C32C1B93ED11E4A4A446172083338AEFA0C960D0035A2FC991F43B189688CD3"
    )

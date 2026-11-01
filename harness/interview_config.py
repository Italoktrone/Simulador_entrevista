"""Carga del escenario de entrevista y validación de sus referencias."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from harness.json_loader import load_json
from harness.profile import CandidateProfile, load_profile
from harness.schema_validator import validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config/interviews/basica.json"
DEFAULT_CANDIDATE_PATH = PROJECT_ROOT / "data/candidates/candidato_junior.json"
DEFAULT_JOB_PATH = PROJECT_ROOT / "data/jobs/desarrollador_junior.json"
CONFIG_SCHEMA_PATH = PROJECT_ROOT / "schemas/interview_config.schema.json"
JOB_SCHEMA_PATH = PROJECT_ROOT / "schemas/job.schema.json"


class InterviewConfigError(ValueError):
    """Los documentos son válidos por separado, pero sus referencias difieren."""

    def __init__(self, path: str, rule: str, detail: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"Escenario incompatible en {path}: {detail}")


@dataclass(frozen=True, slots=True)
class InterviewSetup:
    """Datos preparados y protegidos; todavía sin estado de conversación."""

    candidate: CandidateProfile
    _config_json: str = field(repr=False)
    _job_json: str = field(repr=False)

    def config_dict(self) -> dict[str, Any]:
        """Devuelve una copia independiente de las preferencias validadas."""
        return json.loads(self._config_json)

    def job_dict(self) -> dict[str, Any]:
        """Devuelve una copia independiente de la descripción del puesto."""
        return json.loads(self._job_json)


def load_interview_setup(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    candidate_path: str | Path = DEFAULT_CANDIDATE_PATH,
    job_path: str | Path = DEFAULT_JOB_PATH,
) -> InterviewSetup:
    """Carga tres archivos elegidos y comprueba su correspondencia.

    Las rutas predeterminadas pertenecen al escenario inicial del proyecto y
    no dependen de la carpeta actual. Se pueden proporcionar otras rutas;
    no se buscan ni se crean archivos a partir de un identificador.
    Cada carga crea instantáneas nuevas, sin iniciar sesión ni consultar un LLM.
    """
    config = load_json(config_path)
    validate_data(config, load_json(CONFIG_SCHEMA_PATH))
    candidate = load_profile(candidate_path)
    job = load_json(job_path)
    validate_data(job, load_json(JOB_SCHEMA_PATH))

    if config["candidate_id"] != candidate.candidate_id:
        raise InterviewConfigError(
            "/configuration/candidate_id", "candidate_mismatch",
            "El candidato de la configuración no coincide con el perfil cargado."
        )
    if config["job_id"] != job["job_id"]:
        raise InterviewConfigError(
            "/configuration/job_id", "job_mismatch",
            "El puesto de la configuración no coincide con la oferta cargada."
        )
    if candidate.to_dict()["target_job_id"] != job["job_id"]:
        raise InterviewConfigError(
            "/candidate/target_job_id", "target_job_mismatch",
            "El puesto objetivo del candidato no coincide con la oferta cargada."
        )

    candidate.assert_source_unchanged()
    return InterviewSetup(
        candidate=candidate,
        _config_json=json.dumps(config, ensure_ascii=False, allow_nan=False),
        _job_json=json.dumps(job, ensure_ascii=False, allow_nan=False),
    )

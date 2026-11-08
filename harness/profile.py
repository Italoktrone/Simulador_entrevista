"""Coherencia, carga protegida e integridad del perfil ficticio."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from harness.json_loader import load_json, load_json_with_bytes
from harness.schema_validator import validate_data


DEFAULT_PROFILE_SCHEMA = Path(__file__).resolve().parents[1] / "schemas/candidate.schema.json"


class ProfileConsistencyError(ValueError):
    """La estructura es válida, pero sus antecedentes son incompatibles."""

    def __init__(self, path: str, rule: str, detail: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"Perfil incoherente en {path}: {detail}")


class ProfileIntegrityError(ValueError):
    """El archivo original cambió o no se puede comprobar su integridad."""

    def __init__(self, path: Path, rule: str, detail: str) -> None:
        self.path = path
        self.rule = rule
        super().__init__(f"No se pudo verificar el perfil '{path}': {detail}")


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """Instantánea validada que se obtiene mediante load_profile.

    El contenido interno es una cadena inmutable y queda fuera de repr.
    to_dict devuelve una copia independiente para los módulos que la necesiten.
    """

    source_path: Path
    source_sha256: str
    _snapshot_json: str = field(repr=False)

    @property
    def candidate_id(self) -> str:
        return self.to_dict()["candidate_id"]

    @property
    def scenario_reference_date(self) -> str:
        return self.to_dict()["scenario_reference_date"]

    def to_dict(self) -> dict[str, Any]:
        """Devuelve datos nuevos, sin exponer un diccionario interno mutable."""
        return json.loads(self._snapshot_json)

    def to_public_resume(self) -> dict[str, Any]:
        """Genera una copia con campos profesionales autorizados para el CV.

        La selección es explícita tanto en los campos principales como en los
        anidados. Los antecedentes internos restantes no se copian a esta vista.
        """
        data = self.to_dict()
        experience = []
        for employer in data["work_experience"]:
            roles = []
            for role in employer["roles"]:
                periods = role.get("schedule_periods", [])
                responsibilities = list(role.get("responsibilities", []))
                for period in periods:
                    responsibilities.extend(period["responsibilities"])
                roles.append({
                    "title": role["title"],
                    "start_month": role["start_month"],
                    "end_month": role["end_month"],
                    "responsibilities": list(dict.fromkeys(responsibilities)),
                    "schedule_periods": [
                        {
                            "start_month": period["start_month"],
                            "end_month": period["end_month"],
                            "schedule": period["schedule"],
                        }
                        for period in periods
                    ],
                })
            experience.append({"organization": employer["organization"], "roles": roles})
        return {
            "candidate_id": data["candidate_id"],
            "name": data["name"],
            "professional_summary": data["professional_summary"],
            "education": [
                {
                    key: record[key]
                    for key in (
                        "institution", "degree", "start_month", "end_month",
                        "graduation_month", "status",
                    )
                }
                for record in data["education"]
            ],
            "work_experience": experience,
            "technical_skills": [item["area"] for item in data["technical_knowledge"]],
            "tools_used": list(data["tools_used"]),
            "projects": [
                {
                    key: project[key]
                    for key in (
                        "name", "kind", "description", "start_month", "end_month",
                        "technologies_used", "personal_contributions",
                    )
                }
                for project in data["projects"]
            ],
        }

    def assert_source_unchanged(self) -> None:
        """Compara los bytes actuales con la huella tomada durante la carga."""
        try:
            raw_bytes = self.source_path.read_bytes()
        except FileNotFoundError as error:
            raise ProfileIntegrityError(
                self.source_path, "source_missing", "El archivo original ya no existe."
            ) from error
        except OSError as error:
            raise ProfileIntegrityError(
                self.source_path, "source_unreadable", "No se puede leer el archivo original."
            ) from error
        if hashlib.sha256(raw_bytes).hexdigest().upper() != self.source_sha256:
            raise ProfileIntegrityError(
                self.source_path, "source_changed", "La huella del archivo original cambió."
            )


def _month(value: str, path: str) -> date:
    try:
        return date.fromisoformat(value + "-01")
    except ValueError as error:
        raise ProfileConsistencyError(
            path, "invalid_month", "El mes o año no existe en el calendario."
        ) from error


def _period(record: dict, path: str, reference: date) -> tuple[date, date]:
    start = _month(record["start_month"], path + "/start_month")
    end = _month(record["end_month"], path + "/end_month")
    if start > end:
        raise ProfileConsistencyError(
            path, "reversed_period", "El inicio del periodo es posterior a su término."
        )
    if end > reference:
        raise ProfileConsistencyError(
            path, "future_period", "El periodo termina después del mes de referencia."
        )
    return start, end


def _index_records(records: list, key: str, base: str, paths: dict) -> dict:
    indexed = {}
    for position, record in enumerate(records):
        identifier = record[key]
        path = f"{base}/{position}"
        if identifier in paths:
            raise ProfileConsistencyError(
                path + "/" + key,
                "duplicate_id",
                "El identificador ya pertenece a otro registro."
            )
        paths[identifier] = path
        indexed[identifier] = record
    return indexed


def _require_reference(identifier: str, records: dict, path: str) -> None:
    if identifier not in records:
        raise ProfileConsistencyError(
            path, "missing_reference", "No existe el registro al que apunta la referencia."
        )


def _check_schedules(role: dict, path: str, bounds: tuple, reference: date) -> None:
    if "schedule_periods" not in role:
        return
    base = path + "/schedule_periods"
    periods = [
        (*_period(period, f"{base}/{index}", reference), index)
        for index, period in enumerate(role["schedule_periods"])
    ]
    ordered = sorted(periods, key=lambda item: item[0])
    if ordered[0][0] != bounds[0] or ordered[-1][1] != bounds[1]:
        raise ProfileConsistencyError(
            base, "schedule_boundaries", "Las jornadas no cubren los límites del cargo."
        )
    for previous, current in zip(ordered, ordered[1:]):
        current_path = f"{base}/{current[2]}/start_month"
        if current[0] <= previous[1]:
            raise ProfileConsistencyError(
                current_path, "schedule_overlap", "Dos jornadas incluyen el mismo mes."
            )
        previous_month = previous[1].year * 12 + previous[1].month
        current_month = current[0].year * 12 + current[0].month
        if current_month != previous_month + 1:
            raise ProfileConsistencyError(
                current_path, "schedule_gap", "Hay meses del cargo sin una jornada definida."
            )


def validate_profile_data(profile: dict[str, Any], schema: dict[str, Any]) -> None:
    """Valida estructura y relaciones del perfil, sin modificarlo ni acceder a archivos.

    Los periodos mensuales incluyen ambos extremos y se comparan con el mes
    de referencia del escenario, no con la fecha de ejecución. Se permiten
    estudios y trabajos simultáneos. El significado de los relatos y la
    correspondencia con un archivo de puesto externo requieren otros controles.
    """
    validate_data(profile, schema)
    try:
        scenario_date = date.fromisoformat(profile["scenario_reference_date"])
    except ValueError as error:
        raise ProfileConsistencyError(
            "/scenario_reference_date", "invalid_date", "La fecha no existe en el calendario."
        ) from error
    reference = scenario_date.replace(day=1)

    paths = {}
    education = _index_records(profile["education"], "education_id", "/education", paths)
    experience = _index_records(
        profile["work_experience"], "experience_id", "/work_experience", paths
    )
    projects = _index_records(profile["projects"], "project_id", "/projects", paths)
    situations = _index_records(
        profile["behavioral_situations"], "situation_id", "/behavioral_situations", paths
    )
    achievements = _index_records(profile["achievements"], "achievement_id", "/achievements", paths)
    roles = {}
    role_owners = {}
    for experience_id, record in experience.items():
        group = _index_records(record["roles"], "role_id", paths[experience_id] + "/roles", paths)
        roles.update(group)
        role_owners.update({identifier: experience_id for identifier in group})

    bounds = {}
    for identifier, record in education.items():
        path = paths[identifier]
        bounds[identifier] = _period(record, path, reference)
        graduation_path = path + "/graduation_month"
        graduation = _month(record["graduation_month"], graduation_path)
        if graduation < bounds[identifier][1]:
            raise ProfileConsistencyError(
                graduation_path, "graduation_before_end", "La titulación precede al término de los estudios."
            )
        if graduation > reference:
            raise ProfileConsistencyError(
                graduation_path, "future_graduation", "La titulación es posterior al mes de referencia."
            )
    for identifier, role in roles.items():
        bounds[identifier] = _period(role, paths[identifier], reference)
        _check_schedules(role, paths[identifier], bounds[identifier], reference)

    for identifier, project in projects.items():
        path = paths[identifier]
        project_bounds = _period(project, path, reference)
        if project["kind"] == "Profesional":
            _require_reference(project["experience_id"], experience, path + "/experience_id")
            _require_reference(project["role_id"], roles, path + "/role_id")
            if role_owners[project["role_id"]] != project["experience_id"]:
                raise ProfileConsistencyError(
                    path + "/role_id", "reference_mismatch", "El cargo pertenece a otra experiencia."
                )
            context = bounds[project["role_id"]]
        else:
            _require_reference(project["education_id"], education, path + "/education_id")
            context = bounds[project["education_id"]]
        if project_bounds[0] < context[0] or project_bounds[1] > context[1]:
            raise ProfileConsistencyError(
                path, "project_outside_context", "El proyecto queda fuera del periodo de su cargo o formación."
            )

    for identifier, study in education.items():
        path = paths[identifier] + "/final_project_id"
        _require_reference(study["final_project_id"], projects, path)
        project = projects[study["final_project_id"]]
        if project["kind"] != "Académico" or project["education_id"] != identifier:
            raise ProfileConsistencyError(
                path, "reference_mismatch", "El proyecto de título no corresponde a esta formación."
            )
    for identifier, role in roles.items():
        for index, project_id in enumerate(role.get("project_ids", [])):
            path = f"{paths[identifier]}/project_ids/{index}"
            _require_reference(project_id, projects, path)
            project = projects[project_id]
            if project["kind"] != "Profesional" or project["role_id"] != identifier:
                raise ProfileConsistencyError(
                    path, "reference_mismatch", "El proyecto no corresponde a este cargo."
                )
    for project in projects.values():
        if project["kind"] == "Profesional":
            role = roles[project["role_id"]]
            if "project_ids" in role and project["project_id"] not in role["project_ids"]:
                raise ProfileConsistencyError(
                    paths[project["role_id"]] + "/project_ids",
                    "reference_mismatch",
                    "El cargo declara proyectos, pero omite uno que lo referencia."
                )

    for identifier, situation in situations.items():
        if "project_id" in situation:
            _require_reference(situation["project_id"], projects, paths[identifier] + "/project_id")
    for identifier, achievement in achievements.items():
        path = paths[identifier]
        if "project_id" in achievement:
            _require_reference(achievement["project_id"], projects, path + "/project_id")
        if "situation_id" in achievement:
            _require_reference(achievement["situation_id"], situations, path + "/situation_id")
            situation = situations[achievement["situation_id"]]
            if (
                "project_id" in achievement and "project_id" in situation
                and achievement["project_id"] != situation["project_id"]
            ):
                raise ProfileConsistencyError(
                    path, "reference_mismatch", "El logro y su situación apuntan a proyectos distintos."
                )
    for section in ("professional_competencies", "strengths", "improvement_areas"):
        for index, record in enumerate(profile[section]):
            for position, situation_id in enumerate(record["situation_ids"]):
                _require_reference(
                    situation_id, situations, f"/{section}/{index}/situation_ids/{position}"
                )


def load_profile(
    path: str | Path, schema_path: str | Path = DEFAULT_PROFILE_SCHEMA
) -> CandidateProfile:
    """Lee, valida y conserva una instantánea del perfil con su huella SHA-256.

    La huella se calcula sobre los mismos bytes que se interpretaron. Después
    se vuelve a comprobar el archivo para detectar cambios durante la carga.
    No escribe en el archivo ni sustituye la comprobación al finalizar una
    futura entrevista. El esquema predeterminado se ubica respecto del módulo.
    """
    source_path = Path(path).resolve()
    data, raw_bytes = load_json_with_bytes(source_path)
    schema = load_json(schema_path)
    validate_profile_data(data, schema)
    profile = CandidateProfile(
        source_path=source_path,
        source_sha256=hashlib.sha256(raw_bytes).hexdigest().upper(),
        _snapshot_json=json.dumps(data, ensure_ascii=False, allow_nan=False),
    )
    profile.assert_source_unchanged()
    return profile

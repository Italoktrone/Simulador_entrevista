"""Catálogo cerrado de escenarios: los identificadores nunca se interpretan como rutas."""

from types import MappingProxyType

from harness.interview_config import PROJECT_ROOT, load_interview_setup


CANDIDATES = MappingProxyType({
    "cand-001": ("config/interviews/basica.json", "data/candidates/candidato_junior.json"),
    "cand-002": ("config/interviews/basica-cand-002.json", "data/candidates/candidata_calidad.json"),
    "cand-003": ("config/interviews/basica-cand-003.json", "data/candidates/candidato_datos.json"),
})


class UnknownCandidateError(ValueError):
    """El identificador no pertenece al catálogo de perfiles habilitados."""


def load_candidate_setup(candidate_id="cand-001"):
    try:
        config_path, profile_path = CANDIDATES[candidate_id]
    except (KeyError, TypeError):
        raise UnknownCandidateError("El candidato no pertenece al catálogo.") from None
    setup = load_interview_setup(PROJECT_ROOT / config_path, PROJECT_ROOT / profile_path)
    if setup.candidate.candidate_id != candidate_id:
        raise ValueError("El identificador del catálogo no coincide con su perfil.")
    return setup


def public_candidates():
    entries = []
    for candidate_id in CANDIDATES:
        setup = load_candidate_setup(candidate_id)
        resume = setup.candidate.to_public_resume()
        job = setup.job_dict()
        entries.append({"candidate_id": candidate_id, "name": resume["name"],
                        "professional_summary": resume["professional_summary"],
                        "job_id": job["job_id"], "job_title": job["title"], "is_fictional": True})
    return entries

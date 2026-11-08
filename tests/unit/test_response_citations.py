"""No publicar citas inventadas; conservar texto y código que no sean citas."""

import pytest

from harness.llm.client import LLMResponse
from harness.response_validator import ResponseCitationError, validate_response_citations


@pytest.mark.parametrize("text", [
    "Revisé la API [resume.work_experience].",
    "Verifiqué los datos [document_id: resume.work_experience].",
    "Sin cita: mi experiencia consta en el CV.",
    'Código: valores[0], datos["nombre"], [b]texto literal[/b].',
])
def test_accepts_exact_public_ids_and_preserves_other_brackets(text):
    response = LLMResponse(text, "simulado", "ollama", 0.1)
    assert validate_response_citations(response, [{"document_id": "resume.work_experience"}]) is response


@pytest.mark.parametrize("citation", [
    "resume.projects", "resume.work_experience/1/roles/1", "job.organization",
    "document_id: resume.projects", "/work_experience/1/roles/1/responsibilities",
    "data/candidates/candidata_calidad.json#/work_experience/1/roles/1/responsibilities",
    "/candidate_profile/name", "/projects/1/name", "/job_description/title",
    "candidate_profile/work_experience/0/roles/1/title", "candidate_profile.projects.0",
    "job_description/requirements", "work_experience/0/roles/0", "resume/work_experience",
])
def test_rejects_internal_paths_and_sources_not_in_retrieved_passages(citation):
    response = LLMResponse(f"Mi aporte [{citation}].", "simulado", "ollama", 0.1)
    with pytest.raises(ResponseCitationError) as failure:
        validate_response_citations(response, [{"document_id": "resume.work_experience"}])
    assert failure.value.response is response
    assert citation not in str(failure.value)


def test_no_retrieved_documents_does_not_authorize_a_fabricated_citation():
    with pytest.raises(ResponseCitationError):
        validate_response_citations(LLMResponse("Uso SQL [resume.projects].", "simulado", "ollama", 0.1), [])

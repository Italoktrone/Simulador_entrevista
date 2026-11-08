"""Validación acotada de citas; no acredita la fidelidad semántica del texto libre."""

import re

from harness.llm.client import LLMInvalidResponseError, LLMResponse


class ResponseCitationError(LLMInvalidResponseError):
    """Conservar la salida original para auditoría sin publicarla como válida."""

    def __init__(self, response: LLMResponse):
        super().__init__("La respuesta contiene una referencia documental no autorizada.")
        self.response = response


def validate_response_citations(response: LLMResponse, sources: list[dict]) -> LLMResponse:
    """Revisar citas conocidas sin interpretar corchetes de código.

    Un ID permitido identifica un pasaje recuperado, no demuestra que respalde
    la afirmación. Las rutas internas nunca son una forma de cita pública.
    """
    allowed = {source["document_id"] for source in sources}
    for match in re.finditer(r"\[([^\[\]\r\n]+)\]", response.text):
        citation = match[1].strip()
        if citation.startswith("document_id:"):
            citation = citation.removeprefix("document_id:").strip()
            if citation not in allowed:
                raise ResponseCitationError(response)
        elif citation.startswith(("resume.", "job.")):
            if citation not in allowed:
                raise ResponseCitationError(response)
        elif citation.startswith(("data/", "data\\", "candidate_profile/", "candidate_profile.",
                                  "job_description/", "job_description.", "resume/", "job/",
                                  "/candidate_profile/", "/job_description/", "work_experience/",
                                  "/work_experience/", "projects/", "/projects/", "education/", "/education/")):
            raise ResponseCitationError(response)
    return response

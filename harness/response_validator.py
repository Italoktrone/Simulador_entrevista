"""Controles acotados de citas y acciones; no certifican toda la prosa."""

import re

from harness.llm.client import LLMInvalidResponseError, LLMResponse
from harness.behavioral_evidence import _normalized


class ResponseValidationError(LLMInvalidResponseError):
    """Conservar la salida original para auditoría sin publicarla como válida."""

    def __init__(self, response: LLMResponse, message: str):
        super().__init__(message)
        self.response = response


class ResponseCitationError(ResponseValidationError):
    def __init__(self, response: LLMResponse):
        super().__init__(response, "La respuesta contiene una referencia documental no autorizada.")


class ResponseSupportError(ResponseValidationError):
    def __init__(self, response: LLMResponse, reason: str):
        super().__init__(response, "La respuesta atribuye apoyo o acciones no respaldados por el episodio.")
        self.reason = reason


SUPPORT_VALIDATION_VERSION = "1.0.1"


def _affirmed(pattern, text):
    for match in re.finditer(pattern, text):
        prefix = text[max(0, match.start() - 25):match.start()]
        if not re.search(r"\bno(?:\s+(?:lo|la|nosotros|realmente))?\s*$", prefix):
            return True
    return False


def validate_support_claims(response: LLMResponse, selection: dict | None) -> LLMResponse:
    """Rechazar formas explícitas de coautoría/incapacidad no documentadas.

    Control conservador de expresiones conocidas, no validación semántica
    general. Nunca reescribe la respuesta ni repite una generación.
    """
    if selection is None or response.finish_reason == "length":
        return response
    text = _normalized(response.text)
    if not selection["selected"] and selection["missing_directions"]:
        if _affirmed(r"\b(?:ayude|apoye|oriente|he ayudado|he apoyado)\b", text):
            raise ResponseSupportError(response, "unsupported_episode")
        if re.search(r"\b(?:nunca|jamas) he (?:ayudado|apoyado)\b|\bno he ayudado a nadie\b", text):
            raise ResponseSupportError(response, "unsupported_global_absence")
    roles = [r for item in selection["selected"] for r in item["action_roles"]]
    individual = " ".join(_normalized(r["quote"]) for r in roles if r["documented_involvement"] == "candidate_action")
    shared = " ".join(_normalized(r["quote"]) for r in roles if r["documented_involvement"] == "shared_action")
    groups = (
        (r"\b(?:cambio|corrigio|modifico|implemento|desarrollo)\b", r"\b(?:cambi|corrig|modific|implement|desarroll)",
         r"\b(?:cambiamos|cambiaron|corregimos|corrigieron|modificamos|modificaron|implementamos|implementaron|desarrollamos|desarrollaron)\b",
         r"(?:cambio|corrigio|modifico|implemento|desarrollo)\b"),
        (r"\b(?:anadio|escribio|creo)\b.{0,55}\bprueba", r"\b(?:anad|escrib|cre)\w*.{0,55}\bprueba",
         r"\b(?:anadimos|anadieron|escribimos|escribieron|creamos|crearon)\b.{0,55}\bprueba",
         r"(?:anadio|escribio|creo)\b.{0,55}\bprueba"),
    )
    for own_pattern, shared_pattern, collective, peer_verb in groups:
        if not re.search(own_pattern, individual) or re.search(shared_pattern, shared):
            continue
        # «Me ayudó a cambiar» puede describir orientación; no equivale a
        # afirmar que el ayudante ejecutó el cambio. Exigir atribución clara.
        peer = r"\b(?:el desarrollador|la desarrolladora|mi companero|mi companera|la analista|mi colega)\s+(?:fue quien\s+)?"
        peer_execution = peer + peer_verb
        if _affirmed(collective, text) or _affirmed(peer_execution, text):
            raise ResponseSupportError(response, "unsupported_shared_execution")
    consulted = any(r["documented_involvement"] == "candidate_consulted_other" for r in roles)
    uncertainty_source = re.search(r"\b(?:no sabia|no pudo|no podia|insegur|dificultad)", individual)
    if consulted and not uncertainty_source and re.search(
        r"\bno sabia como (?:resolver|corregir|cambiar)\b", text
    ):
        raise ResponseSupportError(response, "unsupported_inability")
    return response


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

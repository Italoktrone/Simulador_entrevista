"""Bloquear atribuciones explícitas sin fundamento, sin reescribir salidas."""

import pytest

from harness.behavioral_evidence import select_support_evidence
from harness.candidate_catalog import load_candidate_setup
from harness.llm.client import LLMResponse
from harness.response_validator import ResponseSupportError, validate_support_claims


def plan(candidate="cand-001", question="Cuéntame cuándo necesitaste ayuda de un compañero."):
    return select_support_evidence(load_candidate_setup(candidate).candidate.to_dict(), question)


@pytest.mark.parametrize("text", [
    "Consulté mi propuesta con el desarrollador y cambié la consulta a LEFT JOIN.",
    "El desarrollador me ayudó a revisar la propuesta; yo cambié la consulta y añadí una prueba.",
    "No cambiamos la consulta juntos: la cambié yo, después de consultar mi propuesta.",
    "El desarrollador me ayudó a cambiar la consulta mediante la revisión de mi propuesta; yo apliqué el cambio.",
])
def test_accepts_consultation_with_candidate_owned_execution(text):
    response = LLMResponse(text, "simulado", "ollama", 0.1)
    assert validate_support_claims(response, plan()) is response


@pytest.mark.parametrize("text,reason", [
    ("Consulté mi propuesta, y juntos cambiamos la consulta y añadimos una prueba.", "unsupported_shared_execution"),
    ("El desarrollador cambió la consulta a LEFT JOIN por mí.", "unsupported_shared_execution"),
    ("Mi compañero añadió una prueba de regresión.", "unsupported_shared_execution"),
    ("Después de consultarlo, escribimos una prueba de regresión juntos.", "unsupported_shared_execution"),
    ("No sabía cómo resolver el error, por lo que consulté mi propuesta.", "unsupported_inability"),
])
def test_rejects_unsupported_execution_or_inability_and_keeps_raw_response(text, reason):
    response = LLMResponse(text, "simulado", "ollama", 0.1)
    with pytest.raises(ResponseSupportError) as caught:
        validate_support_claims(response, plan())
    assert caught.value.response is response and caught.value.reason == reason
    assert text not in str(caught.value)


def test_allows_documented_joint_review_and_checks():
    response = LLMResponse("Revisamos ambas versiones y comprobamos el resultado para integrar ambos cambios.", "simulado", "ollama", 0.1)
    assert validate_support_claims(response, plan("cand-003")) is response


def test_hypotheses_are_not_judged_as_historical_claims():
    response = LLMResponse("Si necesitara ayuda, cambiaríamos la consulta después de revisarla.", "simulado", "ollama", 0.1)
    assert validate_support_claims(response, None) is response


@pytest.mark.parametrize("text", ["Ayudé a un compañero a instalar el proyecto.", "Nunca he ayudado a nadie."])
def test_missing_episode_does_not_allow_invention_or_global_denial(text):
    selection = plan("cand-002", "¿Cuándo ayudaste a un compañero?")
    with pytest.raises(ResponseSupportError):
        validate_support_claims(LLMResponse(text, "simulado", "ollama", 0.1), selection)
    response = LLMResponse("No puedo darte un ejemplo concreto de ese tipo.", "simulado", "ollama", 0.1)
    assert validate_support_claims(response, selection) is response

"""Roles de apoyo, hechos seleccionados y aislamiento de la vista del perfil."""

from copy import deepcopy
import json

import pytest

from harness.behavioral_evidence import select_support_evidence, support_profile_view, audit_support_selection
from harness.candidate_catalog import load_candidate_setup
from harness.prompt_builder import build_messages, load_instructions, SCENARIO_DATA_MARKER, SCENARIO_END_MARKER, SUPPORT_DATA_MARKER


QUESTION = "Cuéntame una ocasión en que necesitaste ayuda de un compañero y cómo trabajaron juntos."


@pytest.mark.parametrize("candidate_id,sid", [("cand-001", "S1"), ("cand-002", "S4"), ("cand-003", "S3")])
def test_received_support_uses_exact_evidence_from_its_own_profile(candidate_id, sid):
    setup = load_candidate_setup(candidate_id)
    original = setup.candidate.to_dict()
    before = deepcopy(original)
    plan = select_support_evidence(original, QUESTION)
    assert plan["requested_directions"] == ["received"]
    assert [s["situation_id"] for s in plan["selected"]] == [sid]
    source = next(s for s in original["behavioral_situations"] if s["situation_id"] == sid)
    for evidence in plan["selected"][0]["evidence"]:
        value = source[evidence["field"]]
        assert evidence["quote"] == (value[evidence["index"]] if isinstance(value, list) else value)
    view = support_profile_view(original, plan)
    assert view["behavioral_situations"] == [source]
    assert original == before == setup.candidate.to_dict()
    view["behavioral_situations"][0]["actions"].append("Cambio de una copia")
    assert original == before
    setup.candidate.assert_source_unchanged()


@pytest.mark.parametrize("question", [
    QUESTION, "Describe una situación en la que pediste apoyo a un colega.",
    "¿Cuándo te echaron una mano?", "¿En qué ocasión recibiste orientación?",
    "¿Has tenido que pedirle ayuda a alguien?", "¿Quién te brindó apoyo con una tarea?",
    "No te pregunto cuándo ayudaste a otro; quiero saber cuándo pediste ayuda tú.",
])
def test_received_variants_do_not_select_the_guide_given_to_another_person(question):
    profile = load_candidate_setup().candidate.to_dict()
    plan = select_support_evidence(profile, question)
    assert plan["requested_directions"] == ["received"]
    assert [s["situation_id"] for s in plan["selected"]] == ["S1"]


@pytest.mark.parametrize("question", [
    "¿Qué hiciste cuando un compañero necesitó tu ayuda?", "Cuéntame cuándo ayudaste a alguien.",
    "¿Cómo reaccionaste cuando te pidieron apoyo?", "¿Cuándo echaste una mano a otro compañero?",
])
def test_provided_support_keeps_its_missing_project_and_original_actor(question):
    profile = load_candidate_setup().candidate.to_dict()
    plan = select_support_evidence(profile, question)
    assert plan["requested_directions"] == ["provided"]
    assert plan["selected"][0]["situation_id"] == "S4"
    assert plan["selected"][0]["project_id"] is None and plan["selected"][0]["project_name"] is None


@pytest.mark.parametrize("candidate_id", ["cand-002", "cand-003"])
def test_missing_provided_episode_does_not_relabel_received_support(candidate_id):
    profile = load_candidate_setup(candidate_id).candidate.to_dict()
    plan = select_support_evidence(profile, "¿Cuándo ayudaste a otro compañero?")
    assert plan["missing_directions"] == ["provided"] and not plan["selected"]
    assert not support_profile_view(profile, plan)["behavioral_situations"]
    assert profile["behavioral_situations"]


def test_both_directions_stay_distinct_and_followup_switches_roles():
    profile = load_candidate_setup().candidate.to_dict()
    both = select_support_evidence(profile, "Cuéntame cuándo pediste ayuda y cuándo ayudaste a otro.")
    assert [(s["direction"], s["situation_id"]) for s in both["selected"]] == [("received", "S1"), ("provided", "S4")]
    history = [{"role": "user", "content": "¿Cuándo ayudaste a otro?"},
               {"role": "assistant", "content": "Un compañero no pudo iniciar el proyecto con mi guía."}]
    switched = select_support_evidence(profile, "¿Y cuando fuiste tú quien necesitó ayuda?", history)
    assert switched["requested_directions"] == ["received"] and switched["selected"][0]["situation_id"] == "S1"
    history += [{"role": "user", "content": QUESTION}, {"role": "assistant", "content": "Un relato anterior equivocado sobre la guía."}]
    followup = select_support_evidence(profile, "¿Qué hiciste después y cuál fue el resultado?", history)
    assert followup["history_used"] and followup["selected"][0]["situation_id"] == "S1"
    history += [{"role": "user", "content": "¿Dónde estudiaste?"}, {"role": "assistant", "content": "Respuesta académica."}]
    assert select_support_evidence(profile, "¿Y después?", history) is None


@pytest.mark.parametrize("question", ["¿Qué harías si un compañero te pide ayuda?", "¿Cómo pedirías apoyo?", "¿Qué tecnologías usaste?", "¿Qué hiciste en MesaFaro?"])
def test_hypothetical_and_unrelated_questions_keep_the_full_profile(question):
    profile = load_candidate_setup().candidate.to_dict()
    assert select_support_evidence(profile, question) is None
    assert support_profile_view(profile, None) == profile


def test_no_human_consultation_is_invented_from_a_database_or_documentation_lookup():
    profile = load_candidate_setup().candidate.to_dict()
    profile["behavioral_situations"] = [{"situation_id": "X", "title": "Consultar documentación",
        "context": "Revisó material técnico.", "actions": ["Consultó la documentación y la base de datos."], "outcome": "Completó la consulta."}]
    plan = select_support_evidence(profile, QUESTION)
    assert not plan["selected"] and plan["missing_directions"] == ["received"]


def test_named_project_does_not_move_the_received_help_to_another_project():
    profile = load_candidate_setup().candidate.to_dict()
    plan = select_support_evidence(profile, "¿Cuándo pediste ayuda en Inventario Aula?")
    assert not plan["selected"] and plan["missing_directions"] == ["received"]


def test_foreign_selection_is_rejected_even_when_situation_ids_overlap():
    first = load_candidate_setup().candidate.to_dict()
    other = load_candidate_setup("cand-002").candidate.to_dict()
    with pytest.raises(ValueError, match="candidato"):
        support_profile_view(other, select_support_evidence(first, QUESTION))


def test_prompt_view_removes_unselected_episodes_and_their_linked_records():
    setup = load_candidate_setup()
    original = setup.candidate.to_dict()
    instructions = load_instructions()
    messages = build_messages(setup, QUESTION, instructions=instructions)
    raw = messages[0]["content"].split(SCENARIO_DATA_MARKER, 1)[1].split(SCENARIO_END_MARKER, 1)[0]
    scenario = json.loads(raw)
    plan = json.loads(messages[0]["content"].split(SUPPORT_DATA_MARKER, 1)[1].split("\nFIN_EPISODIOS_DE_APOYO_SELECCIONADOS_JSON", 1)[0])
    assert plan == select_support_evidence(original, QUESTION)
    assert [s["situation_id"] for s in scenario["candidate_profile"]["behavioral_situations"]] == ["S1"]
    assert "Un compañero no pudo iniciar el proyecto con su guía." not in messages[0]["content"]
    assert "Mejorar la guía de instalación local." not in messages[0]["content"]
    assert messages[-1]["content"] == QUESTION and setup.candidate.to_dict() == original
    audit = audit_support_selection(plan)
    assert "quote" not in json.dumps(audit) and audit["selected"] == [{"direction": "received", "situation_id": "S1"}]
    audit["selected"][0]["situation_id"] = "Cambio"
    assert plan["selected"][0]["situation_id"] == "S1"


def test_consulting_a_proposal_does_not_give_the_helper_joint_authorship_of_the_change():
    profile = load_candidate_setup().candidate.to_dict()
    roles = select_support_evidence(profile, QUESTION)["selected"][0]["action_roles"]
    assert [r["documented_involvement"] for r in roles] == [
        "candidate_action", "candidate_action", "candidate_consulted_other", "candidate_action"
    ]
    assert roles[3]["quote"] == profile["behavioral_situations"][0]["actions"][3]
    other = load_candidate_setup("cand-003").candidate.to_dict()
    roles = select_support_evidence(other, QUESTION)["selected"][0]["action_roles"]
    assert [r["documented_involvement"] for r in roles] == ["candidate_action", "shared_action", "shared_action"]


def test_selection_is_not_keyed_to_specific_names_or_situation_ids():
    profile = load_candidate_setup().candidate.to_dict()
    profile["candidate_id"] = "another-profile"
    for index, situation in enumerate(profile["behavioral_situations"]):
        situation["situation_id"] = f"episode-{index}"
    plan = select_support_evidence(profile, QUESTION)
    assert plan["candidate_id"] == "another-profile" and plan["selected"][0]["situation_id"] == "episode-0"

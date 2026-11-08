"""Selección por HTTP, perfiles coherentes y contexto aislado; modelos simulados."""

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker
import pytest

from app.contracts import SessionInput
from app.main import create_app
from harness.candidate_catalog import CANDIDATES, load_candidate_setup, public_candidates, UnknownCandidateError
from harness.document_search import DocumentSearch, GroundedClient
from harness.interview_config import DEFAULT_CANDIDATE_PATH
from harness.llm.client import LLMResponse
from harness.profile import load_profile, ProfileConsistencyError, validate_profile_data, DEFAULT_PROFILE_SCHEMA
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import load_session


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def selected_api(tmp_path):
    requests = {}

    @contextmanager
    def factory(options):
        setup = load_candidate_setup(options.candidate_id)

        class Model:
            def generate(self, messages):
                requests.setdefault(options.candidate_id, []).append(deepcopy(messages))
                return LLMResponse(f"Soy {setup.candidate.to_dict()['name']}.", "simulado", "ollama", 0.01)

        grounded = GroundedClient(Model())
        yield InterviewRuntime(setup, load_instructions(), grounded), grounded

    application = create_app(directory=tmp_path, factory=factory, token=None)
    with TestClient(application) as client:
        yield client, application.state.service, requests, tmp_path


@pytest.mark.parametrize("candidate_id", CANDIDATES)
def test_profile_configuration_public_cv_and_references_are_coherent(candidate_id):
    setup = load_candidate_setup(candidate_id)
    profile = setup.candidate.to_dict()
    resume = setup.candidate.to_public_resume()
    assert profile["candidate_id"] == setup.config_dict()["candidate_id"] == resume["candidate_id"] == candidate_id
    assert profile["target_job_id"] == setup.job_dict()["job_id"]
    assert profile["is_fictional"] is True
    assert len(profile["behavioral_situations"]) >= 4
    assert resume["name"] == profile["name"] and resume["projects"]
    assert not {"behavioral_situations", "strengths", "improvement_areas", "personality", "professional_status"} & resume.keys()
    setup.candidate.assert_source_unchanged()
    for other in CANDIDATES:
        if other != candidate_id:
            foreign = load_candidate_setup(other).candidate.to_dict()
            assert foreign["name"] not in json.dumps(profile, ensure_ascii=False)
            assert all(p["name"] not in json.dumps(resume, ensure_ascii=False) for p in foreign["projects"])


@pytest.mark.parametrize("candidate_id", ["cand-002", "cand-003"])
def test_new_profiles_reject_invalid_chronology_and_foreign_references(candidate_id):
    schema = json.loads(DEFAULT_PROFILE_SCHEMA.read_text(encoding="utf-8"))
    profile = load_candidate_setup(candidate_id).candidate.to_dict()
    invalid = deepcopy(profile)
    invalid["education"][0]["graduation_month"] = "2021-01"
    with pytest.raises(ProfileConsistencyError):
        validate_profile_data(invalid, schema)
    invalid = deepcopy(profile)
    invalid["education"][0]["final_project_id"] = "proj-999"
    with pytest.raises(ProfileConsistencyError):
        validate_profile_data(invalid, schema)


@pytest.mark.parametrize("identifier", ["../escape", "cand-999", "", None])
def test_catalog_rejects_unknown_ids_without_resolving_paths(identifier):
    with pytest.raises(UnknownCandidateError):
        load_candidate_setup(identifier)


def test_catalog_and_preview_have_only_public_information(selected_api):
    client, service, requests, _ = selected_api
    catalog = client.get("/candidates").json()["candidates"]
    assert catalog == public_candidates() == client.get("/metadata").json()["candidates"]
    assert [p["candidate_id"] for p in catalog] == list(CANDIDATES)
    assert len({p["name"] for p in catalog}) == 3
    for candidate in catalog:
        result = client.get(f"/candidates/{candidate['candidate_id']}")
        assert result.status_code == 200
        body = result.json()
        assert body["resume"]["name"] == candidate["name"]
        assert body["resume"]["candidate_id"] == body["candidate_id"] == candidate["candidate_id"]
        assert not any(k in body["resume"] for k in ("behavioral_situations", "personality", "improvement_areas"))
    assert not service.sessions and not requests


def test_three_sessions_use_only_their_own_profile_documents_history_and_file(selected_api):
    client, service, requests, directory = selected_api
    sessions = []
    for candidate_id in CANDIDATES:
        creation = {"request_id": str(uuid4()), "candidate_id": candidate_id, "classify": False, "evaluate": False}
        response = client.post("/sessions", json=creation)
        assert response.status_code == 201
        session = response.json()
        assert session["candidate_id"] == candidate_id == session["resume"]["candidate_id"]
        assert client.post("/sessions", json=creation).json()["session_id"] == session["session_id"]
        run = {"session_id": session["session_id"], "request_id": str(uuid4()), "question": "Cuéntame tus proyectos con Python."}
        reply = client.post("/run", json=run).json()
        assert reply["status"] == "completed" and session["resume"]["name"] in reply["reply"]
        assert client.post("/run", json=run).json() == reply
        assert len(requests[candidate_id]) == 1
        for source in reply["sources"]:
            if source["document_id"].startswith("resume."):
                assert source["source"].split("#")[0] == CANDIDATES[candidate_id][1]
        context = json.dumps(requests[candidate_id], ensure_ascii=False)
        for other in CANDIDATES:
            if other != candidate_id:
                foreign = load_candidate_setup(other).candidate.to_dict()
                assert foreign["name"] not in context
                assert all(p["name"] not in context for p in foreign["projects"])
        assert client.post(f"/sessions/{session['session_id']}/close").status_code == 200
        saved = load_session(directory / "sessions" / f"session-{session['session_id']}.json")
        assert saved["candidate_id"] == candidate_id and len(saved["attempts"]) == 1
        sessions.append(session["session_id"])
    assert len(service.sessions) == len(set(sessions)) == 3


def test_changed_candidate_on_reused_request_id_is_a_conflict(selected_api):
    client, service, _, _ = selected_api
    creation = {"request_id": str(uuid4()), "candidate_id": "cand-002"}
    assert client.post("/sessions", json=creation).status_code == 201
    assert client.post("/sessions", json={**creation, "candidate_id": "cand-003"}).status_code == 409
    assert len(service.sessions) == 1


@pytest.mark.parametrize("candidate_id,status", [("cand-999", 404), ("../../escape", 422), (None, 422), (2, 422)])
def test_invalid_session_selection_creates_no_session(selected_api, candidate_id, status):
    client, service, requests, _ = selected_api
    response = client.post("/sessions", json={"request_id": str(uuid4()), "candidate_id": candidate_id})
    assert response.status_code == status
    assert not service.sessions and not requests


def test_missing_candidate_preserves_original_default_and_wrong_factory_is_rejected(selected_api, tmp_path):
    client, _, _, _ = selected_api
    response = client.post("/sessions", json={"request_id": str(uuid4())})
    assert response.json()["candidate_id"] == "cand-001"
    assert load_profile(DEFAULT_CANDIDATE_PATH).candidate_id == "cand-001"

    @contextmanager
    def wrong_factory(options):
        grounded = GroundedClient(None)
        yield InterviewRuntime(load_candidate_setup(), load_instructions(), grounded), grounded

    application = create_app(directory=tmp_path / "wrong", factory=wrong_factory)
    with TestClient(application) as wrong_client:
        response = wrong_client.post("/sessions", json={"request_id": str(uuid4()), "candidate_id": "cand-002"})
        assert response.status_code == 500 and response.json()["error"]["code"] == "candidate_mismatch"
        assert not application.state.service.sessions


@pytest.mark.parametrize("candidate_id", CANDIDATES)
def test_document_tool_search_is_scoped_to_selected_candidate(selected_api, candidate_id):
    client, _, _, _ = selected_api
    own = load_candidate_setup(candidate_id).candidate.to_dict()
    result = client.post("/tools/search_documents", json={"query": own["projects"][0]["name"], "candidate_id": candidate_id})
    assert result.status_code == 200 and result.json()["sources"]
    assert any(s["document_id"] == "resume.projects" for s in result.json()["sources"])
    docs = json.dumps(DocumentSearch.from_setup(load_candidate_setup(candidate_id)).documents, ensure_ascii=False)
    for other in CANDIDATES:
        if other != candidate_id:
            assert load_candidate_setup(other).candidate.to_dict()["name"] not in docs
    assert client.get("/candidates/cand-999").status_code == 404
    assert client.post("/tools/search_documents", json={"query": "Python", "candidate_id": "cand-999"}).status_code == 404


def test_session_contract_and_published_examples():
    schema = json.loads((ROOT / "agent/session.schema.json").read_text(encoding="utf-8"))
    assert schema == SessionInput.model_json_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    examples = json.loads((ROOT / "agent/examples.json").read_text(encoding="utf-8"))
    for value in examples["valid_sessions"]:
        validator.validate(value)
        SessionInput.model_validate(value)
    for value in examples["invalid_sessions"]:
        assert not validator.is_valid(value)

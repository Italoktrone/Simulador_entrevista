"""API real y arnés real con modelos simulados; sin red ni claves."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker
import pytest
import yaml

from app.contracts import RunInput, RunOutput
from app.main import create_app
from app import service as service_module
from harness.document_search import DocumentSearch, GroundedClient
from harness.interview_config import load_interview_setup
from harness.llm.client import LLMResponse, LLMTimeoutError
from harness.prompt_builder import load_instructions
from harness.runtime import InterviewRuntime
from harness.session_log import load_session
from scripts.check_project import evaluate_retrieval
from tests.integration.test_question_evaluation_flow import make_runtime


ROOT = Path(__file__).resolve().parents[2]


class Model:
    def __init__(self):
        self.requests = []
        self.failure = False

    def generate(self, messages):
        self.requests.append(deepcopy(messages))
        if self.failure:
            raise LLMTimeoutError("DETALLE_PRIVADO")
        citation = " [resume.projects]" if "DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON" in messages[0]["content"] else ""
        return LLMResponse(f"Respuesta documentada{citation}.", "modelo-ficticio", "ollama", 0.01)


@pytest.fixture
def api(tmp_path):
    model = Model()

    @contextmanager
    def factory(options):
        grounded = GroundedClient(model)
        runtime = InterviewRuntime(load_interview_setup(), load_instructions(), grounded)
        yield runtime, grounded

    application = create_app(directory=tmp_path, factory=factory)
    with TestClient(application, raise_server_exceptions=False) as client:
        yield client, application.state.service, model, tmp_path


def start(client):
    payload = {"request_id": str(uuid4()), "classify": False, "evaluate": False}
    response = client.post("/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["session_id"], payload


def question(identifier, **updates):
    return {"session_id": identifier, "request_id": str(uuid4()),
            "question": "¿Qué hiciste en MesaFaro?", **updates}


def test_endpoints_rag_history_idempotency_logs_and_close(api):
    client, service, model, directory = api
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/metadata").json()["agent"]["entrypoint"] == "app.main:app"
    identifier, creation = start(client)
    assert client.post("/sessions", json=creation).json()["session_id"] == identifier
    payload = question(identifier)
    first = client.post("/run", json=payload)
    assert first.status_code == 200
    result = first.json()
    RunOutput.model_validate(result)
    assert result["status"] == "completed" and result["sources"]
    assert "DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON" in model.requests[0][0]["content"]
    assert client.post("/run", json=payload).json() == result
    assert len(model.requests) == 1
    assert client.post("/run", json={**payload, "question": "otra"}).status_code == 409
    second = client.post("/run", json=question(identifier, use_rag=False))
    assert second.json()["questions_asked"] == 2 and not second.json()["sources"]
    assert "DOCUMENTOS_PUBLICOS_RECUPERADOS_JSON" not in model.requests[1][0]["content"]
    assert model.requests[1][-2]["role"] == "assistant"
    events = client.get("/logs", params={"session_id": identifier}).json()["events"]
    assert any(e["run_id"] == payload["request_id"] and e["event"] == "run_finished" for e in events)
    assert events[2]["documents"][0]["sha256"] == result["sources"][0]["sha256"]
    assert payload["question"] not in json.dumps(events)
    assert "candidate_profile" not in client.get(f"/sessions/{identifier}").text
    assert client.post(f"/sessions/{identifier}/close").status_code == 200
    saved = load_session(directory / "sessions" / f"session-{identifier}.json")
    assert len(saved["attempts"]) == 2
    assert client.post("/run", json=question(identifier)).status_code == 409
    assert client.post("/run", json=payload).json() == result
    assert client.post(f"/sessions/{identifier}/close").status_code == 200
    assert len(service.sessions) == 1


def test_invalid_requests_are_rejected_by_http_and_declared_schema(api):
    client, _, model, _ = api
    examples = json.loads((ROOT / "agent/examples.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "agent/input.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for value in examples["valid"]:
        validator.validate(value)
        RunInput.model_validate(value)
    for value in examples["invalid"]:
        assert not validator.is_valid(value)
        response = client.post("/run", json=value)
        assert response.status_code == 422
        assert response.json() == {"error": {"code": "invalid_request"}}
    output_schema = json.loads((ROOT / "agent/output.schema.json").read_text(encoding="utf-8"))
    output_validator = Draft202012Validator(output_schema, format_checker=FormatChecker())
    for value in examples["valid_outputs"]:
        output_validator.validate(value)
        RunOutput.model_validate(value)
    for value in examples["invalid_outputs"]:
        assert not output_validator.is_valid(value)
    assert not model.requests


def test_model_error_is_cached_and_safe(api):
    client, _, model, _ = api
    identifier, _ = start(client)
    model.failure = True
    payload = question(identifier)
    result = client.post("/run", json=payload).json()
    assert result["status"] == "error" and result["questions_asked"] == 1
    assert result["reply"] is None and "DETALLE_PRIVADO" not in json.dumps(result)
    assert client.post("/run", json=payload).json() == result
    assert len(model.requests) == 1


def test_lost_audit_write_retries_without_a_second_generation(api, monkeypatch):
    client, service, model, _ = api
    identifier, _ = start(client)
    original = service.log

    def fail_finished(session_id, request_id, event, **fields):
        if event == "run_finished":
            raise OSError("disco")
        original(session_id, request_id, event, **fields)

    monkeypatch.setattr(service, "log", fail_finished)
    payload = question(identifier)
    assert client.post("/run", json=payload).status_code == 500
    monkeypatch.setattr(service, "log", original)
    assert client.post("/run", json=payload).json()["status"] == "completed"
    assert len(model.requests) == 1


def test_sessions_are_isolated_and_overlapping_turns_are_rejected(api):
    client, service, _, _ = api
    first, _ = start(client)
    second, _ = start(client)
    session = service.get(first)
    with session.lock:
        assert client.post("/run", json=question(first)).status_code == 409
        assert client.post(f"/sessions/{first}/close").status_code == 409
    assert client.post("/run", json=question(second)).status_code == 200
    assert client.get(f"/sessions/{first}").json()["questions_asked"] == 0


def test_session_capacity_and_creation_conflict(api):
    client, service, _, _ = api
    _, creation = start(client)
    assert client.post("/sessions", json={**creation, "evaluate": True}).status_code == 409
    service.max_sessions = 1
    assert client.post("/sessions", json={"request_id": str(uuid4())}).status_code == 503


def test_missing_or_malformed_identifiers_and_json_are_safe(api):
    client, _, _, _ = api
    assert client.get("/logs", params={"session_id": "../../secret"}).status_code == 422
    assert client.get("/logs", params={"session_id": str(uuid4())}).status_code == 404
    assert client.post("/run", content="{malformed", headers={"Content-Type": "application/json"}).status_code == 422
    assert client.post("/run", json=question(str(uuid4()))).status_code == 404


def test_authentication_is_applied_to_all_operations(tmp_path):
    with TestClient(create_app(directory=tmp_path, token="clave-ficticia")) as client:
        assert client.get("/health").status_code == 401
        assert client.get("/health", headers={"Authorization": "Bearer clave-ficticia"}).status_code == 200


def test_full_classifier_and_evaluator_are_presented_in_api(tmp_path):
    @contextmanager
    def factory(options):
        runtime = make_runtime()
        yield runtime, GroundedClient(Model())

    with TestClient(create_app(directory=tmp_path, factory=factory)) as client:
        identifier = client.post("/sessions", json={"request_id": str(uuid4())}).json()["session_id"]
        result = client.post("/run", json=question(identifier, question="¿Has utilizado Git?")).json()
        assert result["status"] == "completed"
        assert result["evaluation"]["status"] == "evaluada"
        handled = client.post("/run", json=question(identifier, question="Hola")).json()
        assert handled["status"] == "handled" and handled["action"] == "no_evaluable"
        assert handled["questions_asked"] == 1


def test_classifier_failure_returns_an_error_without_consuming_a_question(tmp_path):
    from tests.integration.test_pre_response_classification import SemanticClient

    @contextmanager
    def factory(options):
        runtime = make_runtime(semantic=SemanticClient(mode="invalid"))
        yield runtime, GroundedClient(Model())

    with TestClient(create_app(directory=tmp_path, factory=factory)) as client:
        identifier = client.post("/sessions", json={"request_id": str(uuid4())}).json()["session_id"]
        result = client.post("/run", json=question(identifier)).json()
        assert result["status"] == "error" and result["action"] == "error_tecnico"
        assert result["error_code"] == "fallo_clasificacion" and result["questions_asked"] == 0


def test_failed_turn_never_returns_the_previous_evaluation(tmp_path, monkeypatch):
    @contextmanager
    def factory(options):
        yield make_runtime(), GroundedClient(Model())

    application = create_app(directory=tmp_path, factory=factory)
    with TestClient(application) as client:
        identifier = client.post("/sessions", json={"request_id": str(uuid4())}).json()["session_id"]
        assert client.post("/run", json=question(identifier, question="¿Has utilizado Git?")).json()["evaluation"]
        runtime = application.state.service.get(identifier).runtime

        def fail_before_evaluation(*args, **kwargs):
            raise LLMTimeoutError("fallo-ficticio")

        monkeypatch.setattr(runtime, "ask", fail_before_evaluation)
        result = client.post("/run", json=question(identifier)).json()
        assert result["status"] == "error" and result["evaluation"] is None


def test_runtime_factory_releases_all_clients(monkeypatch):
    class ResourceModel(Model):
        provider = "ollama"
        settings = type("Settings", (), {"model": "ficticio", "max_output_tokens": 2048})()
        closed = False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.closed = True

    model = ResourceModel()
    monkeypatch.setattr(service_module, "create_client", lambda: model)
    from app.contracts import SessionInput
    with service_module.runtime_session(SessionInput(request_id=uuid4(), classify=False, evaluate=False)) as (runtime, grounded):
        assert runtime.session_id and grounded.client is model
    assert model.closed


def test_closed_session_retries_a_failed_save(api, monkeypatch):
    client, _, model, directory = api
    identifier, _ = start(client)
    client.post("/run", json=question(identifier))
    original = service_module.save_session
    monkeypatch.setattr(service_module, "save_session", lambda *args: (_ for _ in ()).throw(OSError("disco")))
    assert client.post(f"/sessions/{identifier}/close").status_code == 500
    monkeypatch.setattr(service_module, "save_session", original)
    assert client.post(f"/sessions/{identifier}/close").status_code == 200
    assert (directory / "sessions" / f"session-{identifier}.json").is_file()
    assert len(model.requests) == 1


def test_document_tool_has_provenance_and_no_private_profile_fields(api):
    client, _, _, _ = api
    body = client.post("/tools/search_documents", json={"query": "MesaFaro"}).json()
    assert body["sources"]
    for source in body["sources"]:
        assert hashlib.sha256(source["text"].encode("utf-8")).hexdigest() == source["sha256"]
        assert source["source"].startswith(("data/candidates/", "data/jobs/"))
    assert not client.post("/tools/search_documents", json={"query": "zzzinexistenteqqq"}).json()["sources"]
    search = DocumentSearch.from_setup(load_interview_setup())
    assert not any("internal" in d["document_id"] or "interview_notes" in d["document_id"] for d in search.documents)
    assert evaluate_retrieval()["passed"] == 6


def test_manifest_paths_and_schemas_match_runtime():
    manifest = yaml.safe_load((ROOT / "agent/manifest.yaml").read_text(encoding="utf-8"))
    for field in ("instructions", "input_schema", "output_schema", "tools", "examples"):
        assert (ROOT / manifest[field]).is_file()
    for name, model in (("input", RunInput), ("output", RunOutput)):
        assert json.loads((ROOT / f"agent/{name}.schema.json").read_text(encoding="utf-8")) == model.model_json_schema()


def test_invalid_citation_is_not_published_but_original_is_saved_and_retry_is_idempotent(api, monkeypatch):
    client, _, model, directory = api
    calls = []
    raw = "Utilicé Python [data/candidates/candidato_junior.json#/work_experience/9]."

    def invalid(messages):
        calls.append(messages)
        return LLMResponse(raw, "simulado", "ollama", 0.1)

    monkeypatch.setattr(model, "generate", invalid)
    identifier, _ = start(client)
    payload = question(identifier)
    result = client.post("/run", json=payload).json()
    assert result["status"] == "error" and result["reply"] is None
    assert client.post("/run", json=payload).json() == result and len(calls) == 1
    assert client.post(f"/sessions/{identifier}/close").status_code == 200
    saved = load_session(directory / "sessions" / f"session-{identifier}.json")
    assert saved["attempts"][0]["response"]["text"] == raw
    assert saved["attempts"][0]["status"] == "error"
    assert saved["attempts"][0]["issues"][0]["code"] == "invalid_response"


def test_behavioral_selection_audit_belongs_to_each_cached_request(api, monkeypatch):
    client, service, model, _ = api

    def generated(messages):
        model.requests.append(deepcopy(messages))
        return LLMResponse("Consulté mi propuesta antes de aplicar el cambio.", "simulado", "ollama", 0.1)

    monkeypatch.setattr(model, "generate", generated)
    identifier, _ = start(client)
    received = question(identifier, question="Cuéntame una ocasión en que necesitaste ayuda de un compañero y cómo trabajaron juntos.")
    original_log = service.log
    first_failure = True

    def fail_one_log(session_id, request_id, event, **fields):
        nonlocal first_failure
        if request_id == received["request_id"] and event == "run_finished" and first_failure:
            first_failure = False
            raise OSError("Fallo de auditoría provocado")
        return original_log(session_id, request_id, event, **fields)

    monkeypatch.setattr(service, "log", fail_one_log)
    assert client.post("/run", json=received).status_code == 500
    provided = question(identifier, question="¿Qué hiciste cuando un compañero necesitó tu ayuda?")
    assert client.post("/run", json=provided).json()["status"] == "completed"
    assert client.post("/run", json=received).json()["status"] == "completed"
    assert len(model.requests) == 2
    assert "Un compañero no pudo iniciar el proyecto con su guía." not in model.requests[0][0]["content"]
    events = client.get("/logs", params={"session_id": identifier}).json()["events"]
    finished = {e["run_id"]: e["behavioral_selection"] for e in events if e["event"] == "run_finished"}
    assert finished[received["request_id"]]["selected"] == [{"direction": "received", "situation_id": "S1"}]
    assert finished[provided["request_id"]]["selected"] == [{"direction": "provided", "situation_id": "S4"}]
    assert all(e["candidate_id"] == "cand-001" and "quote" not in json.dumps(e) for e in finished.values())

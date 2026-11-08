"""API local para el cliente Godot; ejecutar con un único proceso Uvicorn."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import secrets
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import yaml

from app.contracts import RunInput, RunOutput, SearchInput, SessionInput
from app.service import InterviewService, ROOT, ServiceError, runtime_session
from harness.document_search import DocumentSearch
from harness.candidate_catalog import load_candidate_setup, public_candidates, UnknownCandidateError


def create_app(*, directory=None, factory=runtime_session, token=None):
    service = InterviewService(Path(directory) if directory is not None else ROOT / "outputs/api", factory)
    api_token = os.environ.get("INTERVIEW_API_TOKEN", "") if token is None else token

    @asynccontextmanager
    async def lifespan(application):
        yield
        service.shutdown()

    def authorize(authorization: str | None = Header(default=None)):
        if api_token and not secrets.compare_digest(authorization or "", f"Bearer {api_token}"):
            raise ServiceError(401, "unauthorized")

    application = FastAPI(title="Simulador de entrevistas", version="1.0.0", lifespan=lifespan,
                          dependencies=[Depends(authorize)])
    application.state.service = service

    @application.exception_handler(ServiceError)
    async def service_error(request: Request, error: ServiceError):
        return JSONResponse({"error": {"code": error.code}}, status_code=error.status)

    @application.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        return JSONResponse({"error": {"code": "invalid_request"}}, status_code=422)

    @application.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception):
        return JSONResponse({"error": {"code": "internal_error"}}, status_code=500)

    @application.get("/health")
    def health():
        return {"status": "ok", "api_version": "1.0.0", "model_readiness": "not_probed"}

    @application.get("/metadata")
    def metadata():
        return {"agent": yaml.safe_load((ROOT / "agent/manifest.yaml").read_text(encoding="utf-8")),
                "tools": yaml.safe_load((ROOT / "agent/tools.yaml").read_text(encoding="utf-8")),
                "session_storage": "single_process_memory", "api_version": "1.0.0",
                "candidates": public_candidates()}

    def candidate_setup(candidate_id):
        try:
            return load_candidate_setup(candidate_id)
        except UnknownCandidateError:
            raise ServiceError(404, "candidate_not_found") from None

    @application.get("/candidates")
    def candidates():
        return {"candidates": public_candidates()}

    @application.get("/candidates/{candidate_id}")
    def candidate_info(candidate_id: str):
        setup = candidate_setup(candidate_id)
        return {"candidate_id": setup.candidate.candidate_id,
                "resume": setup.candidate.to_public_resume(), "job": setup.job_dict()}

    @application.post("/sessions", status_code=201)
    def start(payload: SessionInput):
        return service.start(payload)

    @application.get("/sessions/{session_id}")
    def session_info(session_id: UUID):
        with service.exclusive(session_id) as session:
            return service.public(session)

    @application.post("/sessions/{session_id}/close")
    def close_session(session_id: UUID):
        return service.close(session_id)

    @application.post("/run", response_model=RunOutput)
    def run(payload: RunInput):
        return service.run(payload)

    @application.get("/logs")
    def logs(session_id: UUID):
        return {"session_id": str(session_id), "events": service.logs(session_id)}

    @application.post("/tools/search_documents")
    def search_documents(payload: SearchInput):
        setup = candidate_setup(payload.candidate_id)
        setup.candidate.assert_source_unchanged()
        return {"sources": DocumentSearch.from_setup(setup).search(payload.query, payload.limit)}

    return application


app = create_app()

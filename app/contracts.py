"""Contratos compartidos por HTTP, ejemplos y el cliente de Godot."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


Question = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=4000, pattern=r"\S")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SessionInput(Contract):
    request_id: UUID
    classify: bool = Field(default=True, strict=True)
    evaluate: bool = Field(default=True, strict=True)


class RunInput(Contract):
    session_id: UUID
    request_id: UUID
    question: Question
    use_rag: bool = Field(default=True, strict=True)


class SearchInput(Contract):
    query: Question
    limit: int = Field(default=3, ge=1, le=5, strict=True)


class Source(Contract):
    document_id: str
    title: str
    source: str
    sha256: str
    text: str


class RunOutput(Contract):
    api_version: Literal["1.0.0"] = "1.0.0"
    session_id: UUID
    request_id: UUID
    status: Literal["completed", "handled", "error"]
    reply: str | None
    action: str
    questions_asked: int = Field(ge=0, le=20)
    max_questions: int = Field(ge=1, le=20)
    closed: bool
    sources: list[Source]
    evaluation: dict | None
    error_code: str | None

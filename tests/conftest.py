"""Aislar sesiones y bloquear transportes HTTP reales durante pytest."""

import httpx
import pytest

from harness import session_log


@pytest.fixture(autouse=True)
def isolated_session_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(session_log, "DEFAULT_SESSIONS_DIR", tmp_path / "sessions")


@pytest.fixture(autouse=True)
def block_real_http(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError("HTTP real bloqueado en pytest; utiliza MockTransport.")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)

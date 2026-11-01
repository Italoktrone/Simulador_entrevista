"""Aislar los archivos de sesiones que genere la aplicación durante pytest."""

import pytest

from harness import session_log


@pytest.fixture(autouse=True)
def isolated_session_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(session_log, "DEFAULT_SESSIONS_DIR", tmp_path / "sessions")

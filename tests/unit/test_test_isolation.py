"""La protección de pytest debe detener HTTP real antes de abrir conexiones."""

import httpx
import pytest


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434/api/chat", "https://example.invalid/"])
def test_real_http_is_blocked_for_local_and_external_clients(url):
    with pytest.raises(RuntimeError, match="HTTP real bloqueado en pytest"):
        with httpx.Client(trust_env=False) as client:
            client.get(url)

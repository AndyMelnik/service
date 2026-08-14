import pytest
from fastapi.testclient import TestClient

import app as service


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVICE_TOKENS", "invite-a,invite-b")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/api/v1")
    monkeypatch.setenv("DAILY_QUOTA", "80")
    monkeypatch.setenv("DATA_PATH", str(tmp_path / "store.json"))
    monkeypatch.setenv("TIMESTAMP_SKEW", "120")
    monkeypatch.setenv("ADMIN_TOKEN", "admin-secret")
    monkeypatch.setenv("TRUST_PROXY", "false")
    service.ADMIN_SESSIONS.clear()
    service.ADMIN_LOGIN_ATTEMPTS.clear()
    service.API_RATE_ATTEMPTS.clear()
    service.EVENTS.clear()
    return TestClient(service.app, raise_server_exceptions=False)


@pytest.fixture
def auth():
    return {"Authorization": "Bearer invite-a"}


@pytest.fixture
def mock_llm(monkeypatch):
    async def fake(_action, text, _extras):
        return f"cleaned:{text}"

    monkeypatch.setattr(service, "call_llm", fake)

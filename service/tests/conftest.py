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
    service.MODEL_STATUS_CACHE["at"] = 0.0
    service.MODEL_STATUS_CACHE["iso"] = ""
    service.MODEL_STATUS_CACHE["payload"] = []
    monkeypatch.setattr(
        service,
        "llm_model_statuses",
        lambda force=False: [
            {
                "role": "Primary",
                "model": "openai/gpt-4o-mini",
                "ok": True,
                "state": "available",
                "detail": "HTTP 200",
            },
            {
                "role": "Fallback 1",
                "model": "nvidia/nemotron-3-super-120b-a12b:free",
                "ok": True,
                "state": "available",
                "detail": "HTTP 200",
            },
            {
                "role": "Fallback 2",
                "model": "google/gemma-4-26b-a4b-it",
                "ok": False,
                "state": "unavailable",
                "detail": "HTTP 404",
            },
        ],
    )
    service._RESOLVED_DATA_PATH = None
    service._RESOLVED_DATA_FROM = None
    return TestClient(service.app, raise_server_exceptions=False)


@pytest.fixture
def auth():
    return {"Authorization": "Bearer invite-a"}


@pytest.fixture
def mock_llm(monkeypatch):
    async def fake(_action, text, _extras):
        return f"cleaned:{text}"

    monkeypatch.setattr(service, "call_llm", fake)

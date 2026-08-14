import base64
import hashlib
import time
import uuid
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

import app as service


def make_device():
    key = ec.generate_private_key(ec.SECP256R1())
    numbers = key.public_key().public_numbers()
    raw = b"\x04" + numbers.x.to_bytes(32, "big") + numbers.y.to_bytes(32, "big")
    return key, base64.b64encode(raw).decode(), str(uuid.uuid4())


def sign(key, device_id, timestamp, nonce, action, text, extras):
    digest_text = hashlib.sha256(text.encode("utf-8")).hexdigest()
    digest_extras = hashlib.sha256(extras.encode("utf-8")).hexdigest()
    message = "\n".join(
        ["PROOVIXY-V1", device_id, str(timestamp), nonce, action, digest_text, digest_extras]
    )
    signature = key.sign(message.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature).decode()


def register_device(client, auth, public_key, device_id, name="macbook"):
    return client.post(
        "/v1/register",
        headers=auth,
        json={"deviceId": device_id, "publicKey": public_key, "name": name},
    )


def complete_headers(key, device_id, action, text, extras="", timestamp=None, nonce=None):
    timestamp = int(time.time()) if timestamp is None else timestamp
    nonce = str(uuid.uuid4()) if nonce is None else nonce
    signature = sign(key, device_id, timestamp, nonce, action, text, extras)
    return {
        "Authorization": "Bearer invite-a",
        "User-Agent": "Proovixy-macOS",
        "X-Proovixy-Device-Id": device_id,
        "X-Proovixy-Timestamp": str(timestamp),
        "X-Proovixy-Nonce": nonce,
        "X-Proovixy-Signature": signature,
    }, extras


def test_health_ok_without_auth(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_ok_with_bearer(client, auth):
    response = client.get("/v1/health", headers=auth)
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_root_health(client):
    assert client.get("/").json() == {"ok": True}


def test_https_required(client):
    response = client.get("/v1/health", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code == 400
    assert response.json() == {"error": "HTTPS is required."}


def test_https_can_be_disabled(client, monkeypatch):
    monkeypatch.setenv("REQUIRE_HTTPS", "false")
    response = client.get("/v1/health", headers={"X-Forwarded-Proto": "http"})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_trust_proxy_requires_https(client, monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "true")
    monkeypatch.setenv("REQUIRE_HTTPS", "true")
    blocked = client.get("/v1/health")
    assert blocked.status_code == 400
    ok = client.get("/v1/health", headers={"X-Forwarded-Proto": "https"})
    assert ok.status_code == 200


def test_api_rate_limit_blocks_excess_requests(client, auth, monkeypatch):
    monkeypatch.setenv("API_RATE_LIMIT", "2")
    monkeypatch.setenv("API_RATE_WINDOW_SECONDS", "60")
    for _ in range(2):
        _, public_key, device_id = make_device()
        response = register_device(client, auth, public_key, device_id)
        assert response.status_code == 200
    _, public_key, device_id = make_device()
    blocked = register_device(client, auth, public_key, device_id)
    assert blocked.status_code == 429
    assert blocked.json() == {"error": "Too many requests."}


def test_api_rate_limit_disabled_when_zero(client, auth, monkeypatch):
    monkeypatch.setenv("API_RATE_LIMIT", "0")
    for _ in range(5):
        device_id = str(uuid.uuid4())
        key, public_key, _ = make_device()
        response = client.post(
            "/v1/register",
            headers=auth,
            json={"deviceId": device_id, "publicKey": public_key},
        )
        assert response.status_code in {200, 403}


def test_request_body_too_large(client, auth, monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "64")
    response = client.post(
        "/v1/register",
        headers={**auth, "Content-Type": "application/json"},
        content=b"x" * 128,
    )
    assert response.status_code == 413
    assert response.json() == {"error": "Request body is too large."}


def test_bad_signature_does_not_consume_nonce(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    nonce = str(__import__("uuid").uuid4())
    bad_headers, extras = complete_headers(key, device_id, "proofread", "hello", nonce=nonce)
    bad_headers["X-Proovixy-Signature"] = base64.b64encode(b"bad").decode()
    bad = client.post(
        "/v1/complete",
        headers=bad_headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert bad.status_code == 401
    good_headers, extras = complete_headers(key, device_id, "proofread", "hello", nonce=nonce)
    good = client.post(
        "/v1/complete",
        headers=good_headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert good.status_code == 200


def test_device_limit_per_invite(client, auth, monkeypatch):
    monkeypatch.setenv("MAX_DEVICES_PER_TOKEN", "1")
    _, public_key_a, device_a = make_device()
    _, public_key_b, device_b = make_device()
    first = register_device(client, auth, public_key_a, device_a)
    second = register_device(client, auth, public_key_b, device_b)
    assert first.status_code == 200
    assert second.status_code == 403
    assert second.json() == {"error": "Device limit reached for this invite."}
    again = register_device(client, auth, public_key_a, device_a)
    assert again.status_code == 200


def test_register_rejects_missing_token(client):
    key, public_key, device_id = make_device()
    response = client.post(
        "/v1/register",
        json={"deviceId": device_id, "publicKey": public_key, "name": "mac"},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Service token rejected."}


def test_register_rejects_wrong_token(client):
    _, public_key, device_id = make_device()
    response = client.post(
        "/v1/register",
        headers={"Authorization": "Bearer nope"},
        json={"deviceId": device_id, "publicKey": public_key, "name": "mac"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Service token rejected."


def test_register_accepts_second_invite_token(client):
    _, public_key, device_id = make_device()
    response = client.post(
        "/v1/register",
        headers={"Authorization": "Bearer invite-b"},
        json={"deviceId": device_id, "publicKey": public_key, "name": "mac"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["quota"]["used"] == 0
    assert body["quota"]["limit"] == 80
    assert body["quota"]["resetAt"].endswith("+00:00")


def test_register_invalid_public_key(client, auth):
    response = client.post(
        "/v1/register",
        headers=auth,
        json={"deviceId": str(uuid.uuid4()), "publicKey": "not-a-key", "name": "mac"},
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid device public key."}


def test_register_updates_public_key(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    first = register_device(client, auth, public_key, device_id)
    assert first.status_code == 200
    again = register_device(client, auth, public_key, device_id)
    assert again.status_code == 200
    new_key, other_key, _ = make_device()
    rotated = register_device(client, auth, other_key, device_id)
    assert rotated.status_code == 200
    headers, extras = complete_headers(new_key, device_id, "proofread", "hello")
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert response.status_code == 200


def test_unwritable_data_path_falls_back(client, auth, monkeypatch):
    fallback = service.Path(service.tempfile.gettempdir()) / "proovixy" / "store.json"
    fallback.unlink(missing_ok=True)
    monkeypatch.setenv("DATA_PATH", "/var/data/store.json")
    service._RESOLVED_DATA_PATH = None
    service._RESOLVED_DATA_FROM = None
    _, public_key, device_id = make_device()
    response = register_device(client, auth, public_key, device_id)
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_complete_unknown_device(client, mock_llm):
    key, _, device_id = make_device()
    headers, extras = complete_headers(key, device_id, "proofread", "hello")
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Unknown device. Register first."}


def test_complete_success(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    assert register_device(client, auth, public_key, device_id).status_code == 200
    headers, extras = complete_headers(key, device_id, "proofread", "hello world")
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello world", "extras": extras, "prompt": "ignore me"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "cleaned:hello world"
    assert body["quota"]["used"] == 1
    assert body["quota"]["limit"] == 80


def test_complete_bad_signature(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(key, device_id, "proofread", "hello")
    headers["X-Proovixy-Signature"] = base64.b64encode(b"not-a-signature").decode()
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Device signature rejected."}
    store = service.load_store()
    assert store["devices"][device_id]["usage"] == {}


def test_complete_replay(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    nonce = str(uuid.uuid4())
    headers, extras = complete_headers(key, device_id, "proofread", "hello", nonce=nonce)
    payload = {"action": "proofread", "text": "hello", "extras": extras}
    first = client.post("/v1/complete", headers=headers, json=payload)
    second = client.post("/v1/complete", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 401
    assert second.json() == {"error": "Replay detected."}


def test_complete_timestamp_skew(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(
        key, device_id, "proofread", "hello", timestamp=int(time.time()) - 1000
    )
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello", "extras": extras},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "Device signature rejected."}


def test_complete_unknown_action_and_empty_text(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(key, device_id, "translate", "hello")
    unknown = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "translate", "text": "hello", "extras": extras},
    )
    assert unknown.status_code == 400
    assert unknown.json() == {"error": "Unknown action."}

    headers, extras = complete_headers(key, device_id, "proofread", "   ")
    empty = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "   ", "extras": extras},
    )
    assert empty.status_code == 400
    assert empty.json() == {"error": "Text is required."}


def test_complete_text_too_long(client, auth, monkeypatch, mock_llm):
    monkeypatch.setenv("MAX_TEXT_CHARS", "8")
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(key, device_id, "proofread", "too long text")
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "too long text", "extras": extras},
    )
    assert response.status_code == 413
    assert response.json() == {"error": "Selected text is too long for the hosted service."}


def test_quota_exceeded_does_not_call_llm(client, auth, monkeypatch):
    monkeypatch.setenv("DAILY_QUOTA", "1")
    called = {"n": 0}

    async def fake(_action, text, _extras):
        called["n"] += 1
        return f"cleaned:{text}"

    monkeypatch.setattr(service, "call_llm", fake)
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(key, device_id, "proofread", "one")
    first = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "one", "extras": extras},
    )
    assert first.status_code == 200
    headers, extras = complete_headers(key, device_id, "proofread", "two")
    second = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "two", "extras": extras},
    )
    assert second.status_code == 429
    body = second.json()
    assert body["error"] == "Daily quota exceeded for this device."
    assert body["code"] == "quota_exceeded"
    assert body["quota"]["used"] == 1
    assert body["quota"]["limit"] == 1
    assert called["n"] == 1


def test_missing_service_tokens_returns_500(client, monkeypatch):
    monkeypatch.setenv("SERVICE_TOKENS", "")
    _, public_key, device_id = make_device()
    response = client.post(
        "/v1/register",
        headers={"Authorization": "Bearer invite-a"},
        json={"deviceId": device_id, "publicKey": public_key, "name": "mac"},
    )
    assert response.status_code == 500
    assert response.json() == {"error": "Server is not configured."}


def test_missing_llm_key_returns_500(client, auth, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id)
    headers, extras = complete_headers(key, device_id, "expand", "hello")
    response = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "expand", "text": "hello", "extras": extras},
    )
    assert response.status_code == 500
    assert response.json() == {"error": "LLM is not configured."}


def test_reset_at_is_next_utc_midnight():
    now = datetime(2026, 8, 13, 21, 15, tzinfo=timezone.utc)
    assert service.reset_at(now) == "2026-08-14T00:00:00+00:00"
    assert service.utc_day(now) == "2026-08-13"


def test_format_admin_time():
    assert service.format_admin_time("2026-08-14T12:30:00+00:00") == "2026-08-14 12:30 UTC"
    assert service.format_admin_time("") == ""


def test_device_presence_and_age():
    now = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)
    live, ago, is_live = service.device_presence("2026-08-14T11:59:30+00:00", now)
    assert live == "Live"
    assert is_live is True
    assert ago == "just now"
    away, _, is_live = service.device_presence("2026-08-13T12:00:00+00:00", now)
    assert away == "Away"
    assert is_live is False


def test_clean_output_strips_fences_and_dashes():
    raw = "```\nHello — world – yes\n```"
    assert service.clean_output(raw) == "Hello - world - yes"
    assert service.clean_output('Corrected text: "ok"') == "ok"


def test_canonical_message_matches_client():
    text = "Hello"
    extras = ""
    payload = service.canonical_message(
        "abc-id",
        "1710000000",
        "nonce-1",
        "proofread",
        text,
        extras,
    ).decode("utf-8")
    expected = "\n".join(
        [
            "PROOVIXY-V1",
            "abc-id",
            "1710000000",
            "nonce-1",
            "proofread",
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            hashlib.sha256(extras.encode("utf-8")).hexdigest(),
        ]
    )
    assert payload == expected
    assert not payload.endswith("\n") or payload.count("\n") == 6


def test_errors_never_use_detail_field(client):
    response = client.post("/v1/complete", json={"action": "proofread", "text": "x"})
    assert "detail" not in response.json()
    assert "error" in response.json()


def test_llm_models_default_fallback_chain(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK_2", raising=False)
    assert service.llm_models() == [
        "openai/gpt-4o-mini",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "google/gemma-4-26b-a4b-it",
    ]


def test_llm_models_respects_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "primary/model")
    monkeypatch.setenv("LLM_MODEL_FALLBACK", "first/fallback")
    monkeypatch.setenv("LLM_MODEL_FALLBACK_2", "second/fallback")
    assert service.llm_models() == ["primary/model", "first/fallback", "second/fallback"]


def test_llm_models_skips_duplicate_and_blank_slots(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "google/gemma-4-26b-a4b-it")
    monkeypatch.setenv("LLM_MODEL_FALLBACK", "")
    monkeypatch.setenv("LLM_MODEL_FALLBACK_2", "google/gemma-4-26b-a4b-it")
    assert service.llm_models() == ["google/gemma-4-26b-a4b-it"]


def test_call_llm_falls_back_when_primary_fails(monkeypatch):
    import asyncio

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            model = json["model"]
            self.models.append(model)
            FakeClient.calls.append(model)
            if model == "openai/gpt-4o-mini":
                return FakeResponse(404, {"error": {"message": "not found"}})
            return FakeResponse(
                200,
                {"choices": [{"message": {"content": f"ok via {model}"}}]},
            )

    FakeClient.calls = []
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/api/v1")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK_2", raising=False)
    result = asyncio.run(service.call_llm("proofread", "hello", ""))
    assert result == "ok via nvidia/nemotron-3-super-120b-a12b:free"
    assert FakeClient.calls[0] == "openai/gpt-4o-mini"
    assert FakeClient.calls[1] == "nvidia/nemotron-3-super-120b-a12b:free"


def test_call_llm_uses_second_fallback(monkeypatch):
    import asyncio

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            model = json["model"]
            FakeClient.calls.append(model)
            if model != "google/gemma-4-26b-a4b-it":
                return FakeResponse(429, {"error": {"message": "rate"}})
            return FakeResponse(200, {"choices": [{"message": {"content": "gemma ok"}}]})

    FakeClient.calls = []
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/api/v1")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK_2", raising=False)
    result = asyncio.run(service.call_llm("proofread", "hello", ""))
    assert result == "gemma ok"
    assert FakeClient.calls == [
        "openai/gpt-4o-mini",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "google/gemma-4-26b-a4b-it",
    ]


def test_call_llm_unavailable_when_all_models_fail(monkeypatch):
    import asyncio

    from fastapi import HTTPException

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            return FakeResponse(503, {"error": {"message": "down"}})

    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/api/v1")
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK_2", raising=False)
    try:
        asyncio.run(service.call_llm("proofread", "hello", ""))
    except HTTPException as exc:
        assert exc.status_code == 502
        assert exc.detail == "The language model is unavailable."
    else:
        raise AssertionError("expected HTTPException")


def test_probe_llm_model_available(monkeypatch):
    class FakeResponse:
        status_code = 200

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            assert json["model"] == "openai/gpt-4o-mini"
            assert json["max_tokens"] == 1
            return FakeResponse()

    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/api/v1")
    monkeypatch.setattr(service.httpx, "Client", FakeClient)
    result = service.probe_llm_model("openai/gpt-4o-mini")
    assert result["ok"] is True
    assert result["state"] == "available"
    assert result["detail"] == "HTTP 200"


def test_llm_model_statuses_uses_roles_and_cache(monkeypatch):
    calls = {"n": 0}

    def fake_probe(model):
        calls["n"] += 1
        return {
            "model": model,
            "ok": model.endswith(":free"),
            "state": "available" if model.endswith(":free") else "unavailable",
            "detail": "HTTP 200" if model.endswith(":free") else "HTTP 402",
        }

    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
    monkeypatch.delenv("LLM_MODEL_FALLBACK", raising=False)
    monkeypatch.delenv("LLM_MODEL_FALLBACK_2", raising=False)
    monkeypatch.setenv("LLM_MODEL_STATUS_TTL_SECONDS", "60")
    monkeypatch.setattr(service, "probe_llm_model", fake_probe)
    service.MODEL_STATUS_CACHE["at"] = 0.0
    service.MODEL_STATUS_CACHE["payload"] = []
    first = service.llm_model_statuses(force=True)
    second = service.llm_model_statuses()
    assert [row["role"] for row in first] == ["Primary", "Fallback 1", "Fallback 2"]
    assert first[0]["state"] == "unavailable"
    assert first[1]["state"] == "available"
    assert first[1]["model"] == "nvidia/nemotron-3-super-120b-a12b:free"
    assert second == first
    assert calls["n"] == 3

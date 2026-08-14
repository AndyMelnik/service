from tests.test_app import complete_headers, make_device, register_device
from admin_ui import token_ref


def admin_login(client, token="admin-secret"):
    return client.post(
        "/admin/login",
        data={"token": token},
        follow_redirects=False,
    )


def test_admin_hidden_without_token(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "")
    response = client.get("/admin")
    assert response.status_code == 404
    assert response.json() == {"error": "Not found."}


def test_admin_login_page_without_cookie(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Admin token" in response.text
    assert "Daily quota" not in response.text


def test_admin_rejects_wrong_token(client):
    response = admin_login(client, "nope")
    assert response.status_code == 401
    assert "Token rejected." in response.text


def test_admin_shows_limits_tokens_and_sessions(client, auth, mock_llm):
    key, public_key, device_id = make_device()
    register_device(client, auth, public_key, device_id, name="studio-mac")
    headers, extras = complete_headers(key, device_id, "proofread", "hello world")
    complete = client.post(
        "/v1/complete",
        headers=headers,
        json={"action": "proofread", "text": "hello world", "extras": extras},
    )
    assert complete.status_code == 200

    logged_in = admin_login(client)
    assert logged_in.status_code == 303
    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    html = dashboard.text
    assert "Daily quota" in html
    assert ">80<" in html
    assert "Max text" in html
    assert "token 1" in html
    assert token_ref("invite-a") in html
    assert "studio-mac" in html
    assert "1/80" in html
    assert "/v1/complete" in html
    assert "proofread" in html
    assert "invite-a" not in html
    assert "sk-test" not in html
    assert "admin-secret" not in html
    assert "hello world" not in html


def test_admin_accepts_bearer(client):
    response = client.get("/admin", headers={"Authorization": "Bearer admin-secret"})
    assert response.status_code == 200
    assert "Limits" in response.text
    assert "Sessions" in response.text
    assert "Request log" in response.text

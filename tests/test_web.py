"""Tests for the Flask web layer (customer app + admin dashboard).

These exercise auth, CSRF protection and the data flows against a temporary
SQLite database, with no running server required.
"""

from __future__ import annotations

import pytest

from food_processing_system.config import WebConfig

flask = pytest.importorskip("flask")  # skip cleanly if Flask isn't installed

from food_processing_system.web.app import create_app  # noqa: E402


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "web.db"))
    config = WebConfig(
        secret_key="test-key", admin_username="admin", admin_password="pw"
    )
    application = create_app(config)
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def _csrf_from(html: bytes) -> str:
    text = html.decode()
    marker = 'name="csrf_token" value="'
    start = text.index(marker) + len(marker)
    return text[start : text.index('"', start)]


def _admin_login(client):
    token = _csrf_from(client.get("/admin/login").data)
    return client.post(
        "/admin/login",
        data={"username": "admin", "password": "pw", "csrf_token": token},
        follow_redirects=True,
    )


def _register_and_login(client, name="Asha", account="101", password="pw"):
    token = _csrf_from(client.get("/register").data)
    client.post(
        "/register",
        data={
            "name": name,
            "account_no": account,
            "address": "Mumbai",
            "password": password,
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    token = _csrf_from(client.get("/login").data)
    return client.post(
        "/login",
        data={
            "name": name,
            "account_no": account,
            "password": password,
            "csrf_token": token,
        },
        follow_redirects=True,
    )


# --------------------------------------------------------------------------- #
# Public pages
# --------------------------------------------------------------------------- #


def test_home_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Order your favourite food" in resp.data


# --------------------------------------------------------------------------- #
# Admin dashboard
# --------------------------------------------------------------------------- #


def test_admin_requires_login(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_admin_login_rejects_bad_credentials(client):
    token = _csrf_from(client.get("/admin/login").data)
    resp = client.post(
        "/admin/login",
        data={"username": "admin", "password": "nope", "csrf_token": token},
        follow_redirects=True,
    )
    assert b"Invalid username or password" in resp.data


def test_admin_login_requires_csrf(client):
    resp = client.post("/admin/login", data={"username": "admin", "password": "pw"})
    assert resp.status_code == 400


def test_admin_dashboard_after_login(client):
    resp = _admin_login(client)
    assert resp.status_code == 200
    assert b"Overview" in resp.data


# --------------------------------------------------------------------------- #
# Customer flow
# --------------------------------------------------------------------------- #


def test_customer_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_register_requires_csrf(client):
    resp = client.post(
        "/register",
        data={"name": "A", "account_no": "1", "address": "x", "password": "p"},
    )
    assert resp.status_code == 400


def test_register_login_order_and_view(client):
    resp = _register_and_login(client)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data  # dashboard greeting

    # Place an order.
    token = _csrf_from(client.get("/order").data)
    client.post(
        "/order",
        data={
            "food_name": "Pizza",
            "price": "299",
            "address": "Mumbai",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    orders_page = client.get("/my-orders")
    assert b"Pizza" in orders_page.data


def test_order_rejects_bad_price(client):
    _register_and_login(client)
    token = _csrf_from(client.get("/order").data)
    resp = client.post(
        "/order",
        data={
            "food_name": "Pizza",
            "price": "free",
            "address": "Mumbai",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert b"Price must be a valid number" in resp.data


def test_customer_login_rejects_wrong_password(client):
    _register_and_login(client)  # creates account 101
    token = _csrf_from(client.get("/login").data)
    resp = client.post(
        "/login",
        data={
            "name": "Asha",
            "account_no": "101",
            "password": "wrong",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert b"Invalid name, account number or password" in resp.data


def test_rate_submission(client):
    _register_and_login(client)
    token = _csrf_from(client.get("/rate").data)
    resp = client.post(
        "/rate",
        data={"score": "5", "csrf_token": token},
        follow_redirects=True,
    )
    assert b"Thanks for rating" in resp.data


def test_unknown_page_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404

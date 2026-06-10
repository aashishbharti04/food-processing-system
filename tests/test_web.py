"""Tests for the Flask admin dashboard.

These exercise auth, CSRF protection and the data pages against a temporary
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


def _login(client):
    page = client.get("/login")
    token = _csrf_from(page.data)
    return client.post(
        "/login",
        data={"username": "admin", "password": "pw", "csrf_token": token},
        follow_redirects=True,
    )


def _csrf_from(html: bytes) -> str:
    text = html.decode()
    marker = 'name="csrf_token" value="'
    start = text.index(marker) + len(marker)
    return text[start : text.index('"', start)]


def test_dashboard_requires_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_login_rejects_bad_credentials(client):
    page = client.get("/login")
    token = _csrf_from(page.data)
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "wrong", "csrf_token": token},
        follow_redirects=True,
    )
    assert b"Invalid username or password" in resp.data


def test_login_requires_csrf(client):
    resp = client.post("/login", data={"username": "admin", "password": "pw"})
    assert resp.status_code == 400


def test_successful_login_reaches_dashboard(client):
    resp = _login(client)
    assert resp.status_code == 200
    assert b"Overview" in resp.data


def test_data_pages_render_after_login(client, app):
    # Seed one customer + order via the same services the app uses.
    with app.app_context():
        from food_processing_system.web.app import _services

        customers, orders, _ = _services()
        customers.register("Asha", 101, "Mumbai", "pw")
        orders.place_order(
            food_name="Pizza",
            price="12.50",
            address="Mumbai",
            customer_name="Asha",
            account_no=101,
        )

    _login(client)
    customers_page = client.get("/customers")
    orders_page = client.get("/orders")
    assert b"Asha" in customers_page.data
    assert b"Pizza" in orders_page.data


def test_unknown_page_returns_404(client):
    _login(client)
    assert client.get("/does-not-exist").status_code == 404

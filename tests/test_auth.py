"""Tests for email/password login and the swimmer/coach role switch."""
import re

import pytest
from flask import Blueprint

from backend.app import create_app
from backend.models import ROLE_COACH, ROLE_SWIMMER, Account, db
from backend.routes.auth import role_required

PASSWORD = "lane-four-2026"


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'swim.db'}",
            "SQLALCHEMY_BINDS": {"auth": f"sqlite:///{tmp_path / 'auth.db'}"},
        }
    )
    # Tiny role-gated routes to exercise role_required.
    probe = Blueprint("probe", __name__)
    probe.add_url_rule("/coach-only", "coach_only", role_required(ROLE_COACH)(lambda: "coach ok"))
    probe.add_url_rule("/swimmer-only", "swimmer_only", role_required(ROLE_SWIMMER)(lambda: "swimmer ok"))
    app.register_blueprint(probe)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _csrf(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def register(client, email="swim@example.com", role=ROLE_SWIMMER, password=PASSWORD, confirm=None):
    return client.post(
        "/register",
        data={
            "csrf_token": _csrf(client, "/register"),
            "email": email,
            "password": password,
            "confirm_password": confirm if confirm is not None else password,
            "role": role,
        },
    )


def login(client, email="swim@example.com", role=ROLE_SWIMMER, password=PASSWORD, **extra):
    return client.post(
        "/login",
        data={"csrf_token": _csrf(client), "email": email, "password": password, "role": role, **extra},
    )


def logout(client):
    return client.post("/logout", data={"csrf_token": _csrf(client, "/")})


def test_accounts_stored_in_separate_database(app, tmp_path):
    client = app.test_client()
    register(client)
    with app.app_context():
        assert db.engines["auth"].url.database == str(tmp_path / "auth.db")
        assert db.engines["auth"].url != db.engine.url
        assert "accounts" in db.inspect(db.engines["auth"]).get_table_names()
        assert "accounts" not in db.inspect(db.engine).get_table_names()


def test_password_is_hashed_not_stored_plain(app, client):
    register(client)
    with app.app_context():
        account = db.session.execute(db.select(Account)).scalar_one()
        assert account.password_hash != PASSWORD
        assert PASSWORD not in account.password_hash
        assert account.check_password(PASSWORD)


@pytest.mark.parametrize(
    "role, landing", [(ROLE_SWIMMER, "/profile"), (ROLE_COACH, "/schools")]
)
def test_register_logs_in_with_role(client, role, landing):
    resp = register(client, email=f"{role}@example.com", role=role)
    assert resp.status_code == 302
    assert resp.headers["Location"] == landing
    with client.session_transaction() as sess:
        assert sess["role"] == role


def test_email_is_case_insensitive_and_unique(client):
    register(client, email="Swim@Example.com")
    logout(client)
    resp = register(client, email="swim@example.com")
    assert resp.status_code == 400
    assert b"already exists" in resp.data
    assert login(client, email="SWIM@example.COM").status_code == 302


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"email": "not-an-email"}, b"valid email"),
        ({"password": "short", "confirm": "short"}, b"at least 8"),
        ({"confirm": "something-else"}, b"don&#39;t match"),
    ],
)
def test_register_validation(client, kwargs, message):
    resp = register(client, **kwargs)
    assert resp.status_code == 400
    assert message in resp.data


def test_login_wrong_password_is_generic(client):
    register(client)
    logout(client)
    for resp in (login(client, password="wrong-password"), login(client, email="nobody@example.com")):
        assert resp.status_code == 401
        assert b"Incorrect email or password" in resp.data


def test_login_with_wrong_role_switch_is_rejected(client):
    register(client, email="coach@example.com", role=ROLE_COACH)
    logout(client)
    resp = login(client, email="coach@example.com", role=ROLE_SWIMMER)
    assert resp.status_code == 401
    assert b"Coach account" in resp.data
    with client.session_transaction() as sess:
        assert "account_id" not in sess
    assert login(client, email="coach@example.com", role=ROLE_COACH).status_code == 302


def test_role_required_gates_by_role(client):
    assert client.get("/coach-only").status_code == 302  # not logged in -> login page
    register(client, role=ROLE_SWIMMER)
    assert client.get("/swimmer-only").data == b"swimmer ok"
    assert client.get("/coach-only").status_code == 403
    logout(client)
    register(client, email="coach@example.com", role=ROLE_COACH)
    assert client.get("/coach-only").data == b"coach ok"
    assert client.get("/swimmer-only").status_code == 403


def test_logout_clears_session(client):
    register(client)
    assert b"Log out" in client.get("/").data
    logout(client)
    with client.session_transaction() as sess:
        assert "account_id" not in sess
    assert b"Log in" in client.get("/").data


def test_post_without_csrf_token_is_rejected(client):
    resp = client.post("/login", data={"email": "a@example.com", "password": PASSWORD, "role": ROLE_SWIMMER})
    assert resp.status_code == 400


@pytest.mark.parametrize("next_url", ["https://evil.example", "//evil.example", "/\\evil.example"])
def test_login_ignores_offsite_next(client, next_url):
    register(client)
    logout(client)
    resp = login(client, next=next_url)
    assert resp.headers["Location"] == "/profile"


def test_login_follows_local_next(client):
    register(client)
    logout(client)
    assert login(client, next="/schools/2").headers["Location"] == "/schools/2"

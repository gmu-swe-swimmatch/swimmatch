import re

import pytest

from backend import login_throttle
from backend.app import create_app
from backend.models import db as _db

CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("SWIMMATCH_DB_PATH", str(tmp_path / "test.db"))
    app = create_app({"TESTING": True, "SEED_DEMO_ACCOUNTS": False})
    login_throttle.reset_all()
    yield app
    login_throttle.reset_all()
    with app.app_context():
        _db.session.remove()
        _db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path="/login"):
    """Load a page and return this session's CSRF token."""
    html = client.get(path).get_data(as_text=True)
    return CSRF_RE.search(html).group(1)


def register(client, **overrides):
    data = {
        "name": "Test Swimmer",
        "email": "swimmer@example.com",
        "role": "swimmer",
        "password": "password123",
        "confirm_password": "password123",
    }
    data.update(overrides)
    data["csrf_token"] = csrf(client, "/register")
    return client.post("/register", data=data)


def login(client, email="swimmer@example.com", password="password123", path="/login", **extra):
    data = {"email": email, "password": password, "csrf_token": csrf(client), **extra}
    return client.post(path, data=data)


def logout(client):
    return client.post("/logout", data={"csrf_token": csrf(client, "/posts/")})

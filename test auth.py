"""Register / login / logout behaviour."""
import pytest
from sqlalchemy import select

from backend import login_throttle
from backend.models import User, db
from tests.conftest import csrf, login, logout, register


def get_user(app, email):
    with app.app_context():
        return db.session.execute(select(User).where(User.email == email)).scalars().first()


# ---- Registration -------------------------------------------------------------------------

def test_register_swimmer_logs_in_and_goes_to_posts(app, client):
    r = register(client)
    assert r.status_code == 302 and r.location.endswith("/posts/")
    user = get_user(app, "swimmer@example.com")
    assert user is not None and user.role == "swimmer"
    assert client.get("/posts/").get_data(as_text=True).count("Test Swimmer") >= 1


def test_register_coach_goes_to_new_post(client):
    r = register(client, role="coach", email="coach@example.com")
    assert r.status_code == 302 and r.location.endswith("/posts/new")


def test_email_is_normalised(app, client):
    register(client, email="  Mixed@Example.COM ")
    assert get_user(app, "mixed@example.com") is not None


def test_password_is_hashed_not_stored(app, client):
    register(client)
    user = get_user(app, "swimmer@example.com")
    assert user.password_hash != "password123"
    assert user.check_password("password123")


def test_duplicate_email_rejected_case_insensitive(client):
    register(client)
    logout(client)
    r = register(client, email="SWIMMER@example.com")
    assert r.status_code == 400
    assert "already exists" in r.get_data(as_text=True)


@pytest.mark.parametrize("overrides, field_msg", [
    ({"name": ""}, "Name is required"),
    ({"email": "not-an-email"}, "valid email"),
    ({"role": "admin"}, "coach or a swimmer"),
    ({"password": "short", "confirm_password": "short"}, "at least 8"),
    ({"confirm_password": "different123"}, "don&#39;t match"),
])
def test_invalid_registration(app, client, overrides, field_msg):
    r = register(client, **overrides)
    body = r.get_data(as_text=True)
    assert r.status_code == 400
    assert field_msg in body
    assert "password123" not in body  # password never echoed back
    with app.app_context():
        assert db.session.query(User).count() == 0


def test_logged_in_user_cannot_see_register(client):
    register(client)
    r = client.get("/register")
    assert r.status_code == 302


# ---- Login --------------------------------------------------------------------------------

def test_login_success(client):
    register(client)
    logout(client)
    r = login(client, email="Swimmer@Example.com")
    assert r.status_code == 302 and r.location.endswith("/posts/")


def test_wrong_password_and_unknown_email_get_same_message(client):
    register(client)
    logout(client)
    wrong = login(client, password="nope-nope")
    unknown = login(client, email="ghost@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert "Invalid email or password." in wrong.get_data(as_text=True)
    assert "Invalid email or password." in unknown.get_data(as_text=True)


def test_login_redirects_to_safe_next(client):
    register(client)
    logout(client)
    r = login(client, next="/schools")
    assert r.location.endswith("/schools")


@pytest.mark.parametrize("bad_next", ["//evil.com", "https://evil.com", "/\\evil.com"])
def test_login_ignores_offsite_next(client, bad_next):
    register(client)
    logout(client)
    r = login(client, next=bad_next)
    assert r.location.endswith("/posts/")


def test_login_requires_csrf(client):
    register(client)
    logout(client)
    r = client.post("/login", data={"email": "swimmer@example.com", "password": "password123"})
    assert r.status_code == 400


def test_logout_requires_post_and_ends_session(client):
    register(client)
    assert client.get("/logout").status_code == 405
    r = logout(client)
    assert r.status_code == 302
    assert client.get("/posts/new").status_code == 302  # back to login


# ---- Role guards --------------------------------------------------------------------------

def test_visitor_sent_to_login_for_coach_route(client):
    r = client.get("/posts/new")
    assert r.status_code == 302 and "/login?next=" in r.location


def test_swimmer_forbidden_from_coach_route(client):
    register(client)
    assert client.get("/posts/new").status_code == 403


def test_coach_can_open_new_post(client):
    register(client, role="coach", email="coach@example.com")
    assert client.get("/posts/new").status_code == 200


# ---- Failed-login throttle ----------------------------------------------------------------

def test_throttle_blocks_after_limit(app, client):
    register(client)
    logout(client)
    limit = app.config["LOGIN_MAX_FAILURES"]
    for _ in range(limit):
        assert login(client, password="wrong-guess").status_code == 401
    r = login(client)  # even the correct password is refused while blocked
    assert r.status_code == 429
    assert "Too many failed attempts" in r.get_data(as_text=True)
    assert int(r.headers["Retry-After"]) > 0


def test_throttle_is_per_email(app, client):
    register(client)
    logout(client)
    for _ in range(app.config["LOGIN_MAX_FAILURES"]):
        login(client, email="someone-else@example.com", password="x")
    assert login(client).status_code == 302  # the real account is unaffected


def test_success_resets_failure_count(app, client):
    register(client)
    logout(client)
    limit = app.config["LOGIN_MAX_FAILURES"]
    for _ in range(limit - 1):
        login(client, password="wrong-guess")
    assert login(client).status_code == 302
    logout(client)
    for _ in range(limit - 1):
        assert login(client, password="wrong-guess").status_code == 401


def test_throttle_window_expires():
    ip, email = "1.2.3.4", "a@b.co"
    for t in range(5):
        login_throttle.record_failure(ip, email, now=100 + t)
    assert login_throttle.retry_after(ip, email, 5, 60, now=110) > 0
    assert login_throttle.retry_after(ip, email, 5, 60, now=161) == 0
    login_throttle.reset_all()

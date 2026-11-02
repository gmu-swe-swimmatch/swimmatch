"""Auth/session plumbing: Flask-Login setup, role guard, and a minimal CSRF check.

CSRF: we don't use WTForms, so every state-changing request (POST/PUT/PATCH/DELETE) must carry
the per-session token, either as a `csrf_token` form field or an `X-CSRFToken` header.
Templates render it with `{{ csrf_field() }}`.
"""
import hmac
import secrets
from functools import wraps

from flask import abort, request, session
from flask_login import LoginManager, current_user, login_required
from markupsafe import Markup, escape

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"

CSRF_SESSION_KEY = "_csrf_token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@login_manager.user_loader
def load_user(user_id):
    from backend.models import User, db

    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def coach_required(view):
    """Require a logged-in user with the coach role. Visitors -> login page; non-coaches -> 403."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_coach:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def csrf_field():
    return Markup(f'<input type="hidden" name="csrf_token" value="{escape(get_csrf_token())}">')


def _check_csrf():
    if request.method not in UNSAFE_METHODS:
        return
    expected = session.get(CSRF_SESSION_KEY)
    sent = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
    if not expected or not sent or not hmac.compare_digest(expected, sent):
        abort(400, description="Your form session expired. Please go back, refresh and try again.")


def is_safe_redirect(target):
    """Only allow same-site relative paths for ?next= redirects (prevents open redirects)."""
    return bool(target) and target.startswith("/") and not target.startswith("//") and "\\" not in target


def init_security(app):
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    login_manager.init_app(app)
    if app.config.get("CSRF_ENABLED", True):
        app.before_request(_check_csrf)
    app.jinja_env.globals["csrf_field"] = csrf_field
    app.jinja_env.globals["csrf_token"] = get_csrf_token

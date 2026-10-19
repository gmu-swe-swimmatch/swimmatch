"""Email/password login with a swimmer/coach role switch.

Accounts are stored in the separate auth database (see models/account.py).
The logged-in account id and role live in Flask's signed session cookie.

Use the helpers below to gate other routes:

    @login_required                 # any logged-in account
    @role_required(ROLE_COACH)      # coaches only
    @role_required(ROLE_SWIMMER)    # swimmers only
"""
import re
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import select

from backend.models import ROLE_COACH, ROLE_SWIMMER, ROLES, Account, db

auth_bp = Blueprint("auth", __name__)

ROLE_CODES = [code for code, _ in ROLES]
MIN_PASSWORD_LENGTH = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Where each role lands after logging in.
# TODO: point coaches at a coach dashboard once it exists.
HOME_FOR_ROLE = {ROLE_SWIMMER: "pages.profile", ROLE_COACH: "pages.schools"}


# --------------------------------------------------------------------------
# Session helpers
# --------------------------------------------------------------------------
def current_account():
    """Return the logged-in Account, or None. Cached per request."""
    if "account" not in g:
        account = None
        account_id = session.get("account_id")
        if account_id is not None:
            account = db.session.get(Account, account_id)
            # Drop stale sessions (account deleted or role changed).
            if account is None or account.role != session.get("role"):
                session.pop("account_id", None)
                session.pop("role", None)
                account = None
        g.account = account
    return g.account


def _log_in(account):
    session.clear()  # fresh session on login, avoids session fixation
    session["account_id"] = account.id
    session["role"] = account.role
    account.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    g.account = account


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_account() is None:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def role_required(role):
    """Allow only accounts with the given role (ROLE_SWIMMER or ROLE_COACH)."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_account().role != role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


# --------------------------------------------------------------------------
# CSRF (minimal, for the auth forms — swap for Flask-WTF later)
# --------------------------------------------------------------------------
def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@auth_bp.before_request
def _check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, description="Form expired. Please go back, reload and try again.")


def _safe_next(target):
    """Only follow same-site relative redirects (blocks //evil.com and http://...)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return None


def _role_from_form():
    role = request.form.get("role", ROLE_SWIMMER)
    return role if role in ROLE_CODES else ROLE_SWIMMER


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        role = request.args.get("role", ROLE_SWIMMER)
        return render_template(
            "login.html",
            role=role if role in ROLE_CODES else ROLE_SWIMMER,
            email="",
            next=_safe_next(request.args.get("next")),
        )

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = _role_from_form()
    next_url = _safe_next(request.form.get("next"))

    account = db.session.execute(select(Account).where(Account.email == email)).scalar_one_or_none()
    error = None
    if account is None or not account.check_password(password):
        error = "Incorrect email or password."
    elif account.role != role:
        # Credentials were valid, so it's safe to say which switch they need.
        error = f"That's a {account.role_label} account. Switch to {account.role_label} login."

    if error:
        flash(error, "error")
        return render_template("login.html", role=role, email=email, next=next_url), 401

    _log_in(account)
    flash(f"Logged in as {account.email} ({account.role_label}).", "info")
    return redirect(next_url or url_for(HOME_FOR_ROLE[account.role]))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        role = request.args.get("role", ROLE_SWIMMER)
        return render_template(
            "register.html", role=role if role in ROLE_CODES else ROLE_SWIMMER, email=""
        )

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    role = _role_from_form()

    errors = []
    if not EMAIL_RE.match(email) or len(email) > 254:
        errors.append("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password != confirm:
        errors.append("Passwords don't match.")
    if not errors and db.session.execute(
        select(Account.id).where(Account.email == email)
    ).first():
        errors.append("An account with that email already exists. Try logging in.")

    if errors:
        for message in errors:
            flash(message, "error")
        return render_template("register.html", role=role, email=email), 400

    account = Account(email=email, role=role)
    account.set_password(password)
    db.session.add(account)
    db.session.commit()

    _log_in(account)
    flash(f"Welcome to SwimMatch. You're signed up as a {account.role_label}.", "info")
    return redirect(url_for(HOME_FOR_ROLE[account.role]))


@auth_bp.post("/logout")
def logout():
    session.clear()
    g.pop("account", None)
    flash("You've been logged out.", "info")
    return redirect(url_for("pages.index"))

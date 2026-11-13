"""Register / login / logout."""
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from backend import login_throttle
from backend.models import User, db
from backend.security import is_safe_redirect
from backend.validation import validate_registration

auth_bp = Blueprint("auth", __name__)

# Used so a login attempt for an unknown email still spends time hashing (no user enumeration by timing).
_DUMMY_HASH = generate_password_hash("timing-equalizer-not-a-real-password")


def _redirect_after_login():
    target = request.args.get("next") or request.form.get("next")
    if is_safe_redirect(target):
        return redirect(target)
    return redirect(url_for("posts.list_posts"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("posts.list_posts"))

    form, errors = {}, {}
    if request.method == "POST":
        form, errors = validate_registration(request.form)
        if not errors:
            exists = db.session.execute(select(User).where(User.email == form["email"])).first()
            if exists:
                errors["email"] = "An account with that email already exists."
        if not errors:
            user = User(name=form["name"], email=form["email"], role=form["role"])
            user.set_password(form["password"])
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                # Another request registered the same email between our check and the insert.
                db.session.rollback()
                errors["email"] = "An account with that email already exists."
        if not errors:
            login_user(user)
            flash(f"Welcome to SwimMatch, {user.name}!", "success")
            if user.is_coach:
                return redirect(url_for("posts.new_post"))
            return redirect(url_for("posts.list_posts"))
        form.pop("password", None)

    return render_template("auth/register.html", form=form, errors=errors), (400 if errors else 200)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("posts.list_posts"))

    email, error, status = "", None, 200
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        ip = request.remote_addr
        cfg = current_app.config
        wait = login_throttle.retry_after(ip, email, cfg["LOGIN_MAX_FAILURES"], cfg["LOGIN_WINDOW_SECONDS"])
        if wait:
            minutes = max(1, -(-wait // 60))
            error = f"Too many failed attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}."
            status = 429
        else:
            user = db.session.execute(select(User).where(User.email == email)).scalars().first() if email else None
            if user and user.check_password(password):
                login_throttle.clear(ip, email)
                login_user(user, remember=bool(request.form.get("remember")))
                flash(f"Welcome back, {user.name}.", "success")
                return _redirect_after_login()
            if user is None:
                check_password_hash(_DUMMY_HASH, password)
            login_throttle.record_failure(ip, email)
            error, status = "Invalid email or password.", 401

    response = render_template("auth/login.html", email=email, error=error,
                               next=request.values.get("next", ""))
    headers = {"Retry-After": str(wait)} if status == 429 else {}
    return response, status, headers


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("pages.index"))

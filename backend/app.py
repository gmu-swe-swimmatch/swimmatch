"""Flask application factory for SwimMatch."""
import os
from datetime import date

from flask import Flask, render_template

from backend.models import EVENTS, EVENT_LABELS, db

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)


def format_swim_time(seconds):
    """Render a time in seconds as a swim-meet string, e.g. 101.8 -> '1:41.80'."""
    if seconds is None:
        return "—"
    minutes, secs = divmod(round(seconds, 2), 60)
    if minutes:
        return f"{int(minutes)}:{secs:05.2f}"
    return f"{secs:.2f}"


def format_time_gap(seconds):
    """Render a signed difference in seconds, e.g. -0.42 or +1.10."""
    if seconds is None:
        return "—"
    return f"{seconds:+.2f}"


def _sqlite_uri(env_var, default_filename):
    db_path = os.environ.get(env_var, default_filename)
    if not os.path.isabs(db_path):
        db_path = os.path.join(PROJECT_ROOT, db_path)
    return f"sqlite:///{db_path}"


def _database_uri():
    return _sqlite_uri("SWIMMATCH_DB_PATH", "swim.db")


def _auth_database_uri():
    # TODO: this needs to be safer. Login accounts are written to a plain,
    # unencrypted SQLite file on local disk (auth.db). Passwords are hashed,
    # but emails and hashes are readable by anyone with the file. Before
    # production: move to a managed DB with encryption at rest + access
    # controls, require a real SECRET_KEY, HTTPS + secure cookies, rate-limit
    # logins, and add password reset / email verification.
    return _sqlite_uri("SWIMMATCH_AUTH_DB_PATH", "auth.db")


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../frontend/pages",
        static_folder="../frontend/static",
        static_url_path="/static",
    )
    app.config.from_mapping(
        # Local-only default; nothing here is sensitive. Override via .env if you like.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-not-secret"),
        SQLALCHEMY_DATABASE_URI=_database_uri(),
        # Login accounts live in their own database file (see models/account.py).
        SQLALCHEMY_BINDS={"auth": _auth_database_uri()},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from backend.routes import register_blueprints

    register_blueprints(app)

    app.add_template_filter(format_swim_time, "swimtime")
    app.add_template_filter(format_time_gap, "timegap")

    from backend.routes.auth import csrf_token, current_account

    @app.context_processor
    def inject_globals():
        return {
            "EVENTS": EVENTS,
            "EVENT_LABELS": EVENT_LABELS,
            "current_year": date.today().year,
            "current_account": current_account(),
            "csrf_token": csrf_token,
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    with app.app_context():
        db.create_all()
        from backend.seed import seed_if_empty

        seed_if_empty()

    return app

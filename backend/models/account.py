"""Login accounts (email + password), stored in a SEPARATE database.

Accounts live in their own SQLite file (`auth.db` by default) via the
SQLAlchemy bind key "auth", so credentials never share a file with the
swimming data in `swim.db`. See `_auth_database_uri()` in app.py.

Every account has a `role` — the swimmer/coach switch. Swimmers and coaches
will get different functionality, so routes can gate on it with
`role_required(ROLE_SWIMMER)` / `role_required(ROLE_COACH)` (routes/auth.py).

Because the two databases are separate files, `profile_id` can't be a real
foreign key. It's a plain integer pointing at `swimmers.id` or `coaches.id`
depending on `role`; resolve it with `Account.profile()`.
"""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from backend.models import db

ROLE_SWIMMER = "swimmer"
ROLE_COACH = "coach"
ROLES = [(ROLE_SWIMMER, "Swimmer"), (ROLE_COACH, "Coach")]
ROLE_LABELS = dict(ROLES)


def _utcnow():
    return datetime.now(timezone.utc)


class Account(db.Model):
    __bind_key__ = "auth"
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)  # stored lowercased
    # Salted hash (werkzeug scrypt), never the plain password.
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # ROLE_SWIMMER or ROLE_COACH
    # TODO: link accounts to profiles at sign-up (create a Swimmer / Coach row).
    profile_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        db.CheckConstraint(f"role IN ('{ROLE_SWIMMER}', '{ROLE_COACH}')", name="ck_accounts_role"),
    )

    @property
    def is_swimmer(self):
        return self.role == ROLE_SWIMMER

    @property
    def is_coach(self):
        return self.role == ROLE_COACH

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def profile(self):
        """Return the linked Swimmer or Coach from swim.db, or None if not linked yet."""
        if self.profile_id is None:
            return None
        from backend.models import Coach, Swimmer

        model = Swimmer if self.is_swimmer else Coach
        return db.session.get(model, self.profile_id)

    def __repr__(self):
        return f"<Account {self.email} ({self.role})>"

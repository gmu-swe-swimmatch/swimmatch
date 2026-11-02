"""User accounts (coaches and swimmers).

Passwords are only ever stored as werkzeug hashes; there is no plaintext column.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.models import db

ROLE_COACH = "coach"
ROLE_SWIMMER = "swimmer"
ROLES = (ROLE_COACH, ROLE_SWIMMER)


def _utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)  # stored lowercased
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "coach" | "swimmer"
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    posts = db.relationship(
        "Post",
        back_populates="coach",
        cascade="all, delete-orphan",
        order_by="Post.created_at.desc()",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_coach(self):
        return self.role == ROLE_COACH

    @property
    def is_swimmer(self):
        return self.role == ROLE_SWIMMER

    def __repr__(self):
        # Deliberately excludes email/password_hash so reprs are safe to log.
        return f"<User {self.id} {self.role}>"

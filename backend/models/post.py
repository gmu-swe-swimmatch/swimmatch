"""Coach recruiting posts.

Storage note: `recruiting_events` is a JSON list of event codes (e.g. ["100_FREE", "200_IM"])
and `target_times` is a JSON object of {event_code: seconds}. Unlike swimmer times and school
standards (related tables, see swimmer.py), a post's events are always read and written as one
unit with the post and are never queried individually, so JSON columns keep this simpler.
If we later need "find posts recruiting 100 Fly under 50.00", move these into a related table.
"""
from datetime import datetime, timezone

from backend.models import EVENT_LABELS, db

COURSES = ("SCY", "LCM")


def _utcnow():
    return datetime.now(timezone.utc)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    program_name = db.Column(db.String(160), nullable=False)
    division = db.Column(db.String(20), nullable=False)
    recruiting_events = db.Column(db.JSON, nullable=False, default=list)
    target_times = db.Column(db.JSON, nullable=False, default=dict)
    course = db.Column(db.String(3), nullable=False, default="SCY")
    grad_year = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=_utcnow)  # set only when edited

    coach = db.relationship("User", back_populates="posts")

    def event_rows(self):
        """Return [(label, seconds | None)] for the events this post recruits, in post order."""
        times = self.target_times or {}
        return [(EVENT_LABELS.get(code, code), times.get(code)) for code in (self.recruiting_events or [])]

    def is_owned_by(self, user):
        return bool(user and user.is_authenticated and user.id == self.coach_id)

    def __repr__(self):
        return f"<Post {self.id} {self.program_name}>"

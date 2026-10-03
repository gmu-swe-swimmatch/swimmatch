"""Swimmer profile model.

Design note — why a related table instead of a JSON column for event times:
A swimmer is not a single rating; they have a *set* of event -> time pairs.
We store each pair as its own row in `swimmer_event_times` rather than packing
them into a JSON blob because:
  * the matching engine will compare times event-by-event against
    `school_event_standards`, which is a straight SQL join on `event`;
  * we can enforce one time per (swimmer, event, course) with a unique constraint;
  * adding per-time metadata later (meet name, date swum, LCM conversions)
    is just another column, not a JSON schema migration.
The same shape is mirrored on the school side (see school.py).
"""
from datetime import datetime, timezone

from backend.models import EVENTS, db


def _utcnow():
    return datetime.now(timezone.utc)


class Swimmer(db.Model):
    __tablename__ = "swimmers"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True)
    gender = db.Column(db.String(1), default="M")  # "M" / "F" — standards are gender-specific
    grad_year = db.Column(db.Integer)
    hometown = db.Column(db.String(120))
    state = db.Column(db.String(2))
    club_team = db.Column(db.String(120))
    high_school = db.Column(db.String(120))
    gpa = db.Column(db.Float)
    intended_major = db.Column(db.String(120))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    event_times = db.relationship(
        "SwimmerEventTime",
        back_populates="swimmer",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    def times_by_event(self):
        """Return {event_code: seconds} for this swimmer's SCY times."""
        return {t.event: t.time_seconds for t in self.event_times if t.course == "SCY"}

    def ordered_times(self):
        """Return [(code, label, SwimmerEventTime | None)] in canonical event order."""
        by_event = {t.event: t for t in self.event_times if t.course == "SCY"}
        return [(code, label, by_event.get(code)) for code, label in EVENTS]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.full_name,
            "grad_year": self.grad_year,
            "club_team": self.club_team,
            "gpa": self.gpa,
            "times_scy": self.times_by_event(),
        }

    def __repr__(self):
        return f"<Swimmer {self.full_name}>"


class SwimmerEventTime(db.Model):
    __tablename__ = "swimmer_event_times"
    __table_args__ = (db.UniqueConstraint("swimmer_id", "event", "course"),)

    id = db.Column(db.Integer, primary_key=True)
    swimmer_id = db.Column(db.Integer, db.ForeignKey("swimmers.id"), nullable=False, index=True)
    event = db.Column(db.String(20), nullable=False)  # one of EVENT_CODES
    time_seconds = db.Column(db.Float, nullable=False)
    course = db.Column(db.String(3), nullable=False, default="SCY")  # SCY only for now
    meet_name = db.Column(db.String(160))
    swum_on = db.Column(db.Date)

    swimmer = db.relationship("Swimmer", back_populates="event_times")

    def __repr__(self):
        return f"<SwimmerEventTime {self.event} {self.time_seconds}>"

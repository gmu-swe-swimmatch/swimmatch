"""School / swim program model.

Each program has per-event recruiting standards stored in a related table
(`school_event_standards`), mirroring `swimmer_event_times` so the two can be
joined on `event` when matching. See swimmer.py for the reasoning.
"""
from backend.models import EVENTS, db


class School(db.Model):
    __tablename__ = "schools"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    short_name = db.Column(db.String(6), nullable=False)  # monogram on cards
    city = db.Column(db.String(80))
    state = db.Column(db.String(2), index=True)
    division = db.Column(db.String(20), index=True)  # "NCAA D1", "NCAA D2", "NCAA D3", "NAIA"
    conference = db.Column(db.String(120))
    enrollment = db.Column(db.Integer)
    avg_gpa = db.Column(db.Float)
    acceptance_rate = db.Column(db.Float)  # 0–1
    roster_size = db.Column(db.Integer)
    pool = db.Column(db.String(160))
    description = db.Column(db.Text)
    primary_color = db.Column(db.String(7), default="#0a1f3c")
    website = db.Column(db.String(255))

    standards = db.relationship(
        "SchoolEventStandard",
        back_populates="school",
        cascade="all, delete-orphan",
    )
    coaches = db.relationship(
        "Coach",
        back_populates="school",
        cascade="all, delete-orphan",
    )

    @property
    def location(self):
        return f"{self.city}, {self.state}"

    def standards_by_event(self, gender="M"):
        """Return {event_code: SchoolEventStandard} for one gender."""
        return {s.event: s for s in self.standards if s.gender == gender}

    def ordered_standards(self, gender="M"):
        """Return [(code, label, SchoolEventStandard | None)] in canonical event order."""
        by_event = self.standards_by_event(gender)
        return [(code, label, by_event.get(code)) for code, label in EVENTS]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "division": self.division,
            "conference": self.conference,
            "standards_scy": {
                code: {"recruit": s.recruit_time, "walk_on": s.walkon_time}
                for code, s in self.standards_by_event().items()
            },
        }

    def __repr__(self):
        return f"<School {self.name}>"


class SchoolEventStandard(db.Model):
    """Recruiting time standards for one event at one program (SCY, in seconds)."""

    __tablename__ = "school_event_standards"
    __table_args__ = (db.UniqueConstraint("school_id", "event", "gender"),)

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=False, index=True)
    event = db.Column(db.String(20), nullable=False)  # one of EVENT_CODES
    gender = db.Column(db.String(1), nullable=False, default="M")
    recruit_time = db.Column(db.Float, nullable=False)  # time that typically earns a scholarship look
    walkon_time = db.Column(db.Float)  # slower time that may still earn a roster spot

    school = db.relationship("School", back_populates="standards")

    def __repr__(self):
        return f"<SchoolEventStandard {self.school_id} {self.event}>"

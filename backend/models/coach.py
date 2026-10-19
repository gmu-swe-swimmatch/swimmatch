"""Coach model.

A coach belongs to one college program (School). The program is stored as a
foreign key to `schools` so a coach's program details and recruiting standards
are always one join away.
"""
from backend.models import db


class Coach(db.Model):
    __tablename__ = "coaches"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id"), nullable=False, index=True)

    school = db.relationship("School", back_populates="coaches")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.full_name,
            "school_id": self.school_id,
            "school": self.school.name if self.school else None,
        }

    def __repr__(self):
        return f"<Coach {self.full_name}>"

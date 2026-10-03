"""Database models and shared constants."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Canonical event list, in display order. All times are short-course yards (SCY).
# Codes are what get stored in the database; labels are for display.
EVENTS = [
    ("50_FREE", "50 Free"),
    ("100_FREE", "100 Free"),
    ("200_FREE", "200 Free"),
    ("500_FREE", "500 Free"),
    ("100_BACK", "100 Back"),
    ("100_BREAST", "100 Breast"),
    ("100_FLY", "100 Fly"),
    ("200_IM", "200 IM"),
]
EVENT_LABELS = dict(EVENTS)
EVENT_CODES = [code for code, _ in EVENTS]

from backend.models.school import School, SchoolEventStandard  # noqa: E402
from backend.models.swimmer import Swimmer, SwimmerEventTime  # noqa: E402

__all__ = [
    "db",
    "EVENTS",
    "EVENT_LABELS",
    "EVENT_CODES",
    "School",
    "SchoolEventStandard",
    "Swimmer",
    "SwimmerEventTime",
]

"""School search + match endpoints (JSON) and shared helpers.

The page routes in pages.py reuse `search_schools` and `compute_match_score`.
"""
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, select

from backend.models import School, Swimmer, db

schools_bp = Blueprint("schools", __name__, url_prefix="/api/schools")

DIVISIONS = ["NCAA D1", "NCAA D2", "NCAA D3", "NAIA"]

# Shown on every program card until real scoring exists.
PLACEHOLDER_MATCH_SCORE = 78


def search_schools(query="", division="", state=""):
    """Simple filter over programs by text, division and state."""
    stmt = select(School).order_by(School.name)
    if query:
        like = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(School.name.ilike(like), School.city.ilike(like), School.conference.ilike(like))
        )
    if division:
        stmt = stmt.where(School.division == division)
    if state:
        stmt = stmt.where(School.state == state.upper())
    return db.session.execute(stmt).scalars().all()


def available_states():
    stmt = select(School.state).distinct().order_by(School.state)
    return [s for s in db.session.execute(stmt).scalars().all() if s]


def compute_match_score(swimmer, school):
    """Return a 0–100 fit score between a swimmer and a program.

    # TODO: implement multi-event match scoring
    #   - join swimmer.times_by_event() with school.standards_by_event(swimmer.gender)
    #   - per event, score how close the swimmer is to recruit_time / walkon_time
    #   - weight the swimmer's strongest 2–3 events most heavily (programs recruit specialists)
    #   - optionally blend in academic fit (gpa vs avg_gpa), division and location preferences
    """
    return PLACEHOLDER_MATCH_SCORE


@schools_bp.get("/")
def search():
    results = search_schools(
        request.args.get("q", ""),
        request.args.get("division", ""),
        request.args.get("state", ""),
    )
    return jsonify([school.to_dict() for school in results])


@schools_bp.get("/<int:school_id>")
def detail(school_id):
    school = db.get_or_404(School, school_id)
    return jsonify(school.to_dict())


@schools_bp.get("/match/<int:swimmer_id>")
def match(swimmer_id):
    """Rank programs for a swimmer. Stub: every score is the placeholder."""
    swimmer = db.get_or_404(Swimmer, swimmer_id)
    # TODO: implement multi-event match scoring (see compute_match_score) and sort by score.
    results = [
        {"school_id": s.id, "name": s.name, "score": compute_match_score(swimmer, s), "placeholder": True}
        for s in search_schools()
    ]
    return jsonify(results)

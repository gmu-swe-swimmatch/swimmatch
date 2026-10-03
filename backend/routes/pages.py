"""Server-rendered page routes."""
from flask import Blueprint, render_template, request
from sqlalchemy import select

from backend.models import School, Swimmer, db
from backend.routes.schools import (
    DIVISIONS,
    available_states,
    compute_match_score,
    search_schools,
)

pages_bp = Blueprint("pages", __name__)


def current_swimmer():
    # TODO: replace with the logged-in swimmer once auth exists.
    return db.session.execute(select(Swimmer).order_by(Swimmer.id)).scalars().first()


@pages_bp.get("/")
def index():
    swimmer = current_swimmer()
    featured = search_schools()[:3]
    results = [{"school": s, "score": compute_match_score(swimmer, s)} for s in featured]
    return render_template("index.html", featured=results, school_count=len(search_schools()))


@pages_bp.get("/profile")
def profile():
    return render_template("profile.html", swimmer=current_swimmer())


@pages_bp.get("/schools")
def schools():
    filters = {
        "q": request.args.get("q", ""),
        "division": request.args.get("division", ""),
        "state": request.args.get("state", ""),
    }
    swimmer = current_swimmer()
    matches = search_schools(filters["q"], filters["division"], filters["state"])
    results = [{"school": s, "score": compute_match_score(swimmer, s)} for s in matches]
    return render_template(
        "schools.html",
        results=results,
        filters=filters,
        divisions=DIVISIONS,
        states=available_states(),
    )


@pages_bp.get("/schools/<int:school_id>")
def school_detail(school_id):
    school = db.get_or_404(School, school_id)
    swimmer = current_swimmer()
    my_times = swimmer.times_by_event() if swimmer else {}
    gender = swimmer.gender if swimmer else "M"

    rows = []
    for code, label, standard in school.ordered_standards(gender):
        mine = my_times.get(code)
        gap = round(mine - standard.recruit_time, 2) if (mine and standard) else None
        rows.append({"label": label, "mine": mine, "standard": standard, "gap": gap})

    return render_template(
        "school_detail.html",
        school=school,
        swimmer=swimmer,
        rows=rows,
        score=compute_match_score(swimmer, school),
    )

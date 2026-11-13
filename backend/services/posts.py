"""Business logic for coach recruiting posts."""
from sqlalchemy import select

from backend.models import Post, db
from backend.models.post import COURSES
from backend.validation import DIVISIONS, validate_post


def parse_post_filters(division="", course="", grad_year=""):
    """Turn raw filter values from the browse page into clean filters.

    Unknown or empty values are treated as "All" so a bad URL never breaks the page.

    Returns:
        {"division": str, "course": str, "grad_year": int | None}
    """
    division = (division or "").strip()
    course = (course or "").strip().upper()
    grad_year = (grad_year or "").strip()
    return {
        "division": division if division in DIVISIONS else "",
        "course": course if course in COURSES else "",
        "grad_year": int(grad_year) if grad_year.isdigit() else None,
    }


def search_posts(filters):
    """Return the posts that match the given filters, newest first."""
    stmt = select(Post).order_by(Post.created_at.desc(), Post.id.desc())
    if filters["division"]:
        stmt = stmt.where(Post.division == filters["division"])
    if filters["course"]:
        stmt = stmt.where(Post.course == filters["course"])
    if filters["grad_year"] is not None:
        stmt = stmt.where(Post.grad_year == filters["grad_year"])
    return db.session.execute(stmt).scalars().all()


def available_grad_years():
    """Grad years that at least one post uses, so no filter option leads to an empty list."""
    stmt = select(Post.grad_year).distinct().order_by(Post.grad_year)
    return db.session.execute(stmt).scalars().all()


def count_active_filters(filters):
    """How many filters the swimmer has turned on (shown as a badge on the browse page)."""
    return sum(1 for value in filters.values() if value)


def create_post(coach_id, form_data):
    """Create a new post for a coach. Returns (post, errors) tuple.

    Args:
        coach_id: ID of the coach creating the post
        form_data: Form data from request.form

    Returns:
        (post, errors) where errors is {} on success or {field: message} on failure
    """
    data, errors = validate_post(form_data)
    if errors:
        return None, errors

    post = Post(coach_id=coach_id)
    _apply_post_data(post, data)
    db.session.add(post)
    db.session.commit()
    return post, {}


def _apply_post_data(post, data):
    """Apply validated data to a Post object."""
    post.program_name = data["program_name"]
    post.division = data["division"]
    post.course = data["course"]
    post.grad_year = data["grad_year"]
    post.message = data["message"]
    post.recruiting_events = data["recruiting_events"]
    post.target_times = data["target_times"]

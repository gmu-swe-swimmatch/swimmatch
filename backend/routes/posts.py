"""Coach recruiting posts: public browse/view, coach-only create/edit/delete."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from backend.models import Post, db
from backend.models.post import COURSES
from backend.routes.schools import DIVISIONS
from backend.security import coach_required
from backend.services.posts import (
    available_grad_years,
    count_active_filters,
    create_post,
    parse_post_filters,
    search_posts,
)
from backend.validation import grad_year_choices, validate_post

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


def _get_owned_post_or_403(post_id):
    """Load a post and confirm the logged-in user owns it. Called by every edit/delete route."""
    post = db.get_or_404(Post, post_id)
    if post.coach_id != current_user.id:
        abort(403)
    return post


def _form_context(**extra):
    return {"divisions": DIVISIONS, "courses": COURSES, "grad_years": grad_year_choices(), **extra}


def _form_from_post(post):
    """Pre-fill form values from an existing post (times rendered back to 46.50 / 1:41.80)."""
    from backend.app import format_swim_time

    values = {
        "program_name": post.program_name,
        "division": post.division,
        "course": post.course,
        "grad_year": post.grad_year,
        "message": post.message,
    }
    for code in post.recruiting_events or []:
        values[f"event_{code}"] = "on"
        seconds = (post.target_times or {}).get(code)
        values[f"time_{code}"] = format_swim_time(seconds) if seconds is not None else ""
    return values


def _apply(post, data):
    post.program_name = data["program_name"]
    post.division = data["division"]
    post.course = data["course"]
    post.grad_year = data["grad_year"]
    post.message = data["message"]
    post.recruiting_events = data["recruiting_events"]
    post.target_times = data["target_times"]


@posts_bp.get("/")
def list_posts():
    """Browse page: read the filters from the URL, let the service find the posts, render them."""
    # TODO: filtering by event and bookmarking are out of scope for this build.
    filters = parse_post_filters(
        division=request.args.get("division", ""),
        course=request.args.get("course", ""),
        grad_year=request.args.get("grad_year", ""),
    )
    return render_template(
        "posts/list.html",
        posts=search_posts(filters),
        filters=filters,
        active_filters=count_active_filters(filters),
        divisions=DIVISIONS,
        courses=COURSES,
        grad_years=available_grad_years(),
    )


@posts_bp.get("/<int:post_id>")
def view_post(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template("posts/detail.html", post=post)


@posts_bp.route("/new", methods=["GET", "POST"])
@coach_required
def new_post():
    values, errors = {}, {}
    if request.method == "POST":
        values = request.form
        post, errors = create_post(current_user.id, request.form)
        if not errors:
            flash("Your post is live.", "success")
            return redirect(url_for("posts.view_post", post_id=post.id))
    return render_template(
        "posts/form.html", **_form_context(values=values, errors=errors, post=None)
    ), (400 if errors else 200)


@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@coach_required
def edit_post(post_id):
    post = _get_owned_post_or_403(post_id)
    values, errors = _form_from_post(post), {}
    if request.method == "POST":
        values = request.form
        data, errors = validate_post(request.form)
        if not errors:
            _apply(post, data)
            db.session.commit()
            flash("Post updated.", "success")
            return redirect(url_for("posts.view_post", post_id=post.id))
    return render_template(
        "posts/form.html", **_form_context(values=values, errors=errors, post=post)
    ), (400 if errors else 200)


@posts_bp.post("/<int:post_id>/delete")
@coach_required
def delete_post(post_id):
    post = _get_owned_post_or_403(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("posts.list_posts"))

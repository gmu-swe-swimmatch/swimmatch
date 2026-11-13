"""Business logic for coach recruiting posts."""
from backend.models import Post, db
from backend.validation import validate_post


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

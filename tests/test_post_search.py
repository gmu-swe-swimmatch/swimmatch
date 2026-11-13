"""Browse / filter coach posts: business logic in backend/services/posts.py."""
from backend.models import Post, User, db
from backend.services.posts import (
    available_grad_years,
    count_active_filters,
    parse_post_filters,
    search_posts,
)


def _add_posts(app):
    """One coach with three posts that differ by division, course and grad year."""
    with app.app_context():
        coach = User(name="Coach", email="coach@example.com", role="coach")
        coach.set_password("password123")
        db.session.add(coach)
        db.session.flush()
        for program, division, course, year in [
            ("Riverbend", "NCAA D2", "SCY", 2027),
            ("Northfield", "NCAA D2", "LCM", 2028),
            ("Lakeshore", "NCAA D3", "SCY", 2027),
        ]:
            db.session.add(Post(
                coach_id=coach.id, program_name=program, division=division, course=course,
                grad_year=year, message="Recruiting.", recruiting_events=["200_FREE"],
                target_times={"200_FREE": 102.0},
            ))
        db.session.commit()


# ---- parse_post_filters -------------------------------------------------------------------

def test_parse_keeps_valid_values():
    assert parse_post_filters("NCAA D2", "scy", "2027") == {
        "division": "NCAA D2", "course": "SCY", "grad_year": 2027,
    }


def test_parse_treats_unknown_values_as_all():
    assert parse_post_filters("Made Up", "XYZ", "soon") == {
        "division": "", "course": "", "grad_year": None,
    }


def test_count_active_filters():
    assert count_active_filters(parse_post_filters()) == 0
    assert count_active_filters(parse_post_filters("NCAA D2", "", "2027")) == 2


# ---- search_posts / available_grad_years --------------------------------------------------

def test_no_filters_returns_every_post(app):
    _add_posts(app)
    with app.app_context():
        assert len(search_posts(parse_post_filters())) == 3


def test_filters_combine(app):
    _add_posts(app)
    with app.app_context():
        names = [p.program_name for p in search_posts(parse_post_filters("NCAA D2", "SCY", "2027"))]
        assert names == ["Riverbend"]


def test_available_grad_years_are_distinct_and_sorted(app):
    _add_posts(app)
    with app.app_context():
        assert available_grad_years() == [2027, 2028]


# ---- the browse page still works through the route ----------------------------------------

def test_browse_page_shows_filtered_posts(app, client):
    _add_posts(app)
    html = client.get("/posts/?division=NCAA+D3").get_data(as_text=True)
    assert "Lakeshore" in html and "Riverbend" not in html

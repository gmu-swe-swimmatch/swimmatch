"""Feature 1C: messaging between swimmers and coaches."""
import pytest
from sqlalchemy import select

from backend.models import Conversation, Message, Post, User, db
from tests.conftest import csrf, login, logout, register


# ---- Helpers ------------------------------------------------------------------------------

def make_post(app, coach_email="coach@example.com", program="Lakeshore State"):
    """Create a post directly in the DB for the given coach and return its id."""
    with app.app_context():
        coach = db.session.execute(select(User).where(User.email == coach_email)).scalars().one()
        post = Post(
            coach_id=coach.id,
            program_name=program,
            division="NCAA D1",
            recruiting_events=["100_FREE"],
            target_times={"100_FREE": 46.5},
            course="SCY",
            grad_year=2027,
            message="Looking for sprinters.",
        )
        db.session.add(post)
        db.session.commit()
        return post.id


def send_new(client, post_id, body="Hi coach, I swim a 47.2 in the 100 free."):
    token = csrf(client, "/posts/")
    return client.post(f"/messages/new/{post_id}", data={"body": body, "csrf_token": token})


def reply(client, convo_id, body):
    token = csrf(client, "/posts/")
    return client.post(f"/messages/{convo_id}", data={"body": body, "csrf_token": token})


def only_conversation(app):
    with app.app_context():
        return db.session.execute(select(Conversation)).scalars().one().id


@pytest.fixture
def setup(app, client):
    """A coach with one post, then a logged-in swimmer. Returns the post id."""
    register(client, role="coach", email="coach@example.com", name="Coach Carter")
    post_id = make_post(app)
    logout(client)
    register(client, email="swimmer@example.com", name="Sam Swimmer")
    return post_id


# ---- Sending ------------------------------------------------------------------------------

def test_swimmer_can_message_coach(app, client, setup):
    r = send_new(client, setup)
    assert r.status_code == 302
    convo_id = only_conversation(app)
    assert r.location.endswith(f"/messages/{convo_id}")

    page = client.get(f"/messages/{convo_id}").get_data(as_text=True)
    assert "I swim a 47.2" in page
    assert "Coach Carter" in page


def test_second_message_from_same_post_reuses_conversation(app, client, setup):
    send_new(client, setup)
    # Opening "Message coach" again goes straight to the existing thread.
    r = client.get(f"/messages/new/{setup}")
    assert r.status_code == 302
    send_new(client, setup, body="One more question.")
    with app.app_context():
        assert db.session.query(Conversation).count() == 1
        assert db.session.query(Message).count() == 2


@pytest.mark.parametrize("body, msg", [
    ("", "Write a message"),
    ("   ", "Write a message"),
    ("x" * 2001, "2000 characters"),
])
def test_invalid_message_rejected(app, client, setup, body, msg):
    r = send_new(client, setup, body=body)
    assert r.status_code == 400
    assert msg in r.get_data(as_text=True)
    with app.app_context():
        assert db.session.query(Message).count() == 0


def test_message_is_html_escaped(client, setup):
    send_new(client, setup, body="<script>alert(1)</script>")
    page = client.get("/messages/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_message_to_missing_post_404(client, setup):
    assert send_new(client, 9999).status_code == 404


# ---- Coach reads and replies --------------------------------------------------------------

def test_coach_sees_and_replies(app, client, setup):
    send_new(client, setup)
    convo_id = only_conversation(app)
    logout(client)
    login(client, email="coach@example.com")

    inbox = client.get("/messages/").get_data(as_text=True)
    assert "Sam Swimmer" in inbox and "Lakeshore State" in inbox

    r = reply(client, convo_id, "Thanks Sam, send your schedule.")
    assert r.status_code == 302

    # Swimmer sees the reply in their history.
    logout(client)
    login(client)
    page = client.get(f"/messages/{convo_id}").get_data(as_text=True)
    assert "I swim a 47.2" in page and "send your schedule" in page


def test_unread_badge_and_mark_read(app, client, setup):
    send_new(client, setup)
    convo_id = only_conversation(app)
    logout(client)
    login(client, email="coach@example.com")

    assert "1 unread" in client.get("/posts/").get_data(as_text=True)
    client.get(f"/messages/{convo_id}")  # opening the thread marks it read
    assert "unread" not in client.get("/posts/").get_data(as_text=True)
    with app.app_context():
        assert db.session.execute(select(Message)).scalars().one().read_at is not None


def test_own_messages_do_not_count_as_unread(client, setup):
    send_new(client, setup)
    assert "unread" not in client.get("/posts/").get_data(as_text=True)


def test_coach_cannot_start_conversation(app, client, setup):
    logout(client)
    login(client, email="coach@example.com")
    assert client.get(f"/messages/new/{setup}").status_code == 403
    assert send_new(client, setup).status_code == 403


# ---- Privacy ------------------------------------------------------------------------------

def test_other_users_cannot_view_or_reply(app, client, setup):
    send_new(client, setup)
    convo_id = only_conversation(app)
    logout(client)

    # A different swimmer and a different coach are both locked out.
    for role, email in (("swimmer", "other@example.com"), ("coach", "coach2@example.com")):
        register(client, role=role, email=email)
        assert client.get(f"/messages/{convo_id}").status_code == 403
        assert reply(client, convo_id, "sneaky").status_code == 403
        assert "I swim a 47.2" not in client.get("/messages/").get_data(as_text=True)
        logout(client)

    with app.app_context():
        assert db.session.query(Message).count() == 1


@pytest.mark.parametrize("path", ["/messages/", "/messages/new/1", "/messages/1"])
def test_visitors_sent_to_login(client, path):
    r = client.get(path)
    assert r.status_code == 302 and "/login" in r.location


def test_visitor_cannot_post_message(app, client, setup):
    logout(client)
    r = client.post(f"/messages/new/{setup}", data={"body": "hi", "csrf_token": csrf(client, "/login")})
    assert r.status_code == 302 and "/login" in r.location
    with app.app_context():
        assert db.session.query(Message).count() == 0


def test_message_requires_csrf(client, setup):
    r = client.post(f"/messages/new/{setup}", data={"body": "hi"})
    assert r.status_code == 400


# ---- Post page + post deletion ------------------------------------------------------------

def test_post_page_contact_button(app, client, setup):
    page = client.get(f"/posts/{setup}").get_data(as_text=True)
    assert "Message coach" in page
    send_new(client, setup)
    page = client.get(f"/posts/{setup}").get_data(as_text=True)
    assert "View your conversation" in page


def test_deleting_post_keeps_conversation(app, client, setup):
    send_new(client, setup)
    convo_id = only_conversation(app)
    logout(client)
    login(client, email="coach@example.com")
    client.post(f"/posts/{setup}/delete", data={"csrf_token": csrf(client, f"/posts/{setup}")})

    page = client.get(f"/messages/{convo_id}").get_data(as_text=True)
    assert "post removed" in page and "I swim a 47.2" in page

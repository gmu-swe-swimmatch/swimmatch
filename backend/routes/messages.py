"""Messaging between swimmers and coaches (Feature 1C).

Rules:
- You must be logged in for everything here (visitors are sent to the login page).
- Only swimmers can start a conversation, from a coach's recruiting post.
- Coaches read and reply to conversations swimmers started with them.
- A conversation is only visible to its swimmer and coach. Everyone else gets 403.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.models import Conversation, Post, db
from backend.services.messages import (
    conversations_for,
    find_conversation,
    mark_read,
    send_reply,
    start_conversation,
    unread_count,
)
from backend.validation import MESSAGE_MAX_LENGTH

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


@messages_bp.app_context_processor
def inject_unread_count():
    """Unread count for the "Messages" badge in the nav, on every page."""
    if current_user.is_authenticated:
        return {"unread_messages": unread_count(current_user)}
    return {"unread_messages": 0}


def _get_conversation_or_403(conversation_id):
    """Load a conversation and confirm the current user is in it. Used by every thread route."""
    conversation = db.get_or_404(Conversation, conversation_id)
    if not conversation.has_participant(current_user):
        abort(403)
    return conversation


@messages_bp.get("/")
@login_required
def inbox():
    conversations = conversations_for(current_user)
    return render_template("messages/inbox.html", conversations=conversations)


@messages_bp.route("/new/<int:post_id>", methods=["GET", "POST"])
@login_required
def new_message(post_id):
    """Swimmer writes to the coach who made a post."""
    post = db.get_or_404(Post, post_id)
    if not current_user.is_swimmer:
        abort(403)

    existing = find_conversation(current_user.id, post.id)
    if request.method == "GET" and existing:
        # Already talking about this post: go to that thread instead of starting a second one.
        return redirect(url_for("messages.thread", conversation_id=existing.id))

    errors, values = {}, {}
    if request.method == "POST":
        values = request.form
        conversation, errors = start_conversation(current_user, post, request.form)
        if not errors:
            flash(f"Message sent to {post.coach.name}.", "success")
            return redirect(url_for("messages.thread", conversation_id=conversation.id))

    return render_template(
        "messages/new.html", post=post, values=values, errors=errors, max_length=MESSAGE_MAX_LENGTH
    ), (400 if errors else 200)


@messages_bp.route("/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def thread(conversation_id):
    conversation = _get_conversation_or_403(conversation_id)

    errors, values = {}, {}
    if request.method == "POST":
        values = request.form
        _message, errors = send_reply(conversation, current_user, request.form)
        if not errors:
            return redirect(url_for("messages.thread", conversation_id=conversation.id) + "#latest")

    # Opening the thread counts as reading the other person's messages.
    mark_read(conversation, current_user)
    return render_template(
        "messages/thread.html",
        conversation=conversation,
        other=conversation.other_user(current_user),
        values=values,
        errors=errors,
        max_length=MESSAGE_MAX_LENGTH,
    ), (400 if errors else 200)

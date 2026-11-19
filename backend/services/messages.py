"""Business logic for swimmer <-> coach messaging (Feature 1C)."""
from datetime import datetime, timezone

from sqlalchemy import func, or_, select

from backend.models import Conversation, Message, db
from backend.validation import validate_message


def _utcnow():
    return datetime.now(timezone.utc)


def conversations_for(user):
    """All conversations the user is part of, most recently active first."""
    stmt = (
        select(Conversation)
        .where(or_(Conversation.swimmer_id == user.id, Conversation.coach_id == user.id))
        .order_by(Conversation.last_message_at.desc(), Conversation.id.desc())
    )
    return db.session.execute(stmt).scalars().all()


def find_conversation(swimmer_id, post_id):
    """The swimmer's existing conversation about a post, or None."""
    stmt = select(Conversation).where(
        Conversation.swimmer_id == swimmer_id, Conversation.post_id == post_id
    )
    return db.session.execute(stmt).scalars().first()


def start_conversation(swimmer, post, form_data):
    """Swimmer messages the coach who wrote `post`. Returns (conversation, errors).

    If the swimmer already has a conversation about this post, the message is added to it.
    """
    data, errors = validate_message(form_data)
    if errors:
        return None, errors

    conversation = find_conversation(swimmer.id, post.id)
    if conversation is None:
        conversation = Conversation(
            swimmer_id=swimmer.id,
            coach_id=post.coach_id,
            post_id=post.id,
            subject=post.program_name,
        )
        db.session.add(conversation)

    _add_message(conversation, swimmer, data["body"])
    db.session.commit()
    return conversation, {}


def send_reply(conversation, sender, form_data):
    """Add a reply from either participant. Returns (message, errors).

    The route has already checked that `sender` belongs to this conversation.
    """
    data, errors = validate_message(form_data)
    if errors:
        return None, errors
    message = _add_message(conversation, sender, data["body"])
    db.session.commit()
    return message, {}


def mark_read(conversation, user):
    """Mark every message the other person sent in this conversation as read by `user`."""
    now = _utcnow()
    changed = False
    for message in conversation.messages:
        if message.sender_id != user.id and message.read_at is None:
            message.read_at = now
            changed = True
    if changed:
        db.session.commit()


def unread_count(user):
    """Total unread messages sent to `user`, across all their conversations (nav badge)."""
    stmt = (
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            or_(Conversation.swimmer_id == user.id, Conversation.coach_id == user.id),
            Message.sender_id != user.id,
            Message.read_at.is_(None),
        )
    )
    return db.session.execute(stmt).scalar() or 0


def _add_message(conversation, sender, body):
    now = _utcnow()
    message = Message(sender_id=sender.id, body=body, created_at=now)
    conversation.messages.append(message)
    conversation.last_message_at = now
    return message

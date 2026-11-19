"""Messaging between swimmers and coaches (Feature 1C).

A Conversation is always between one swimmer and one coach and is started by the swimmer from
a recruiting post. Each swimmer gets one conversation per post, so contacting the same post
again reopens the existing thread instead of starting a new one.

`subject` keeps a copy of the post's program name so the thread still makes sense if the coach
later deletes the post (post_id is set to NULL in that case, the messages stay).
"""
from datetime import datetime, timezone

from backend.models import db


def _utcnow():
    return datetime.now(timezone.utc)


class Conversation(db.Model):
    __tablename__ = "conversations"
    __table_args__ = (db.UniqueConstraint("swimmer_id", "post_id", name="uq_conversation_swimmer_post"),)

    id = db.Column(db.Integer, primary_key=True)
    swimmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True, index=True)
    subject = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    last_message_at = db.Column(db.DateTime(timezone=True), default=_utcnow, index=True)

    swimmer = db.relationship("User", foreign_keys=[swimmer_id])
    coach = db.relationship("User", foreign_keys=[coach_id])
    post = db.relationship("Post", back_populates="conversations")
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="(Message.created_at, Message.id)",
    )

    def has_participant(self, user):
        """True only for the swimmer and coach in this conversation."""
        return bool(user and user.is_authenticated and user.id in (self.swimmer_id, self.coach_id))

    def other_user(self, user):
        """The person on the other side of the conversation from `user`."""
        return self.coach if user.id == self.swimmer_id else self.swimmer

    def last_message(self):
        return self.messages[-1] if self.messages else None

    def unread_count_for(self, user):
        return sum(1 for m in self.messages if m.sender_id != user.id and m.read_at is None)

    def __repr__(self):
        return f"<Conversation {self.id} swimmer={self.swimmer_id} coach={self.coach_id}>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)  # set when the recipient opens the thread

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")

    def __repr__(self):
        return f"<Message {self.id} conversation={self.conversation_id}>"

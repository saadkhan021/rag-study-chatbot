from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    courses = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class UserCourse(Base):
    """Which courses a user currently has selected (shown in the sidebar).
    Deleting a row here removes it from the sidebar WITHOUT deleting the
    underlying conversation — re-adding the course brings history back."""
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "course_name", name="uq_user_course"),)

    user = relationship("User", back_populates="courses")


class Conversation(Base):
    """One conversation per (user, course) pair — matches the 'one
    continuous conversation per course' decision."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "course_name", name="uq_user_conversation"),)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class MessageFeedback(Base):
    """Thumbs up/down on an assistant message. A thumbs-down can carry a
    free-text note explaining what's wrong — that note gets fed back into
    rag.regenerate_answer() to produce a corrected reply."""
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(String, nullable=False)  # "up" or "down"
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuizAttempt(Base):
    """One row per graded quiz question — the raw log the assessment
    engine writes to. TopicProgress (below) is the aggregated summary
    built from these rows."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    question = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    feedback = Column(String, nullable=False)  # what the grading step said, specifically
    created_at = Column(DateTime, default=datetime.utcnow)


class TopicProgress(Base):
    """Aggregated per (user, course, topic) stats — this is what answers
    'what does this user know and how well.' Updated every time a new
    QuizAttempt is recorded, not recomputed from scratch each time."""
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_name = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    times_tested = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_tested_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "course_name", "topic", name="uq_user_course_topic"),)

    @property
    def accuracy(self) -> float:
        if self.times_tested == 0:
            return 0.0
        return round(self.times_correct / self.times_tested, 2)

    @property
    def is_weak(self) -> bool:
        """A simple, explainable weak-topic rule: tested at least twice
        and under 60% accuracy. Tune this once you have real usage data —
        it's a starting heuristic, not a tuned threshold."""
        return self.times_tested >= 2 and self.accuracy < 0.6
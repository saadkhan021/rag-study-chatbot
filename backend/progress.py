"""
Memory / progress tracking layer.

This module is deliberately separate from rag.py: rag.py answers
questions from course material, this module remembers how the USER is
doing — what's been tested, what they got right or wrong, and which
topics are weak. The assessment engine (Phase 3) will call
record_attempt() every time it grades a question.
"""

from sqlalchemy.orm import Session
import models


def record_attempt(
    db: Session,
    user_id: int,
    course_name: str,
    topic: str,
    question: str,
    user_answer: str,
    is_correct: bool,
    feedback: str,
) -> models.QuizAttempt:
    """Logs one graded question AND updates the rolling per-topic stats.
    Call this from the assessment engine right after grading an answer."""

    attempt = models.QuizAttempt(
        user_id=user_id,
        course_name=course_name,
        topic=topic,
        question=question,
        user_answer=user_answer,
        is_correct=is_correct,
        feedback=feedback,
    )
    db.add(attempt)

    progress = db.query(models.TopicProgress).filter(
        models.TopicProgress.user_id == user_id,
        models.TopicProgress.course_name == course_name,
        models.TopicProgress.topic == topic,
    ).first()

    if not progress:
        progress = models.TopicProgress(
            user_id=user_id,
            course_name=course_name,
            topic=topic,
            times_tested=0,
            times_correct=0,
        )
        db.add(progress)

    progress.times_tested += 1
    if is_correct:
        progress.times_correct += 1
    progress.last_tested_at = attempt.created_at

    db.commit()
    db.refresh(attempt)
    return attempt


def get_progress(db: Session, user_id: int, course_name: str) -> list[models.TopicProgress]:
    """All topics tracked for this user in this course, most recently
    tested first — powers a 'your progress' view."""
    return db.query(models.TopicProgress).filter(
        models.TopicProgress.user_id == user_id,
        models.TopicProgress.course_name == course_name,
    ).order_by(models.TopicProgress.last_tested_at.desc()).all()


def get_weak_topics(db: Session, user_id: int, course_name: str) -> list[models.TopicProgress]:
    """Topics that meet the is_weak rule (see models.py) — this is what
    the planner (Phase 4) will read from to decide what to prioritize."""
    all_progress = get_progress(db, user_id, course_name)
    return [p for p in all_progress if p.is_weak]
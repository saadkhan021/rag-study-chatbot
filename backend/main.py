from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from database import Base, engine, get_db
import models
import schemas
import auth
import rag
import progress

import exam
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Study RAG Assistant API")

# Adjust origins to match your React dev server / production URL.
# Matches any localhost/127.0.0.1 port instead of a fixed list — Vite
# silently picks a new port (5174, 5175, ...) whenever the previous one
# is still held by a leftover process, and a fixed allow_origins list
# breaks every time that happens. In production, set FRONTEND_URL to
# your deployed frontend's exact origin (e.g. https://yourapp.up.railway.app)
# — the dev regex alone won't match a real domain.
_production_origin = os.getenv("FRONTEND_URL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_production_origin] if _production_origin else [],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Without this, any unhandled error (bad Groq model, missing key, etc.)
    returns a bare 'Internal Server Error' text body with no detail — which
    is what made this bug hard to diagnose from the client side. Now the
    real reason comes back as JSON."""
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# Keep this in sync with ingest.py's data/ subfolder names (lowercased).
AVAILABLE_COURSES = [
    "AI", "Agentic AI", "Generative AI", "Computer Science",
    "Software Engineering", "BBA", "Finance",
]
_COURSE_LOOKUP = {c.lower(): c for c in AVAILABLE_COURSES}


def resolve_course_name(course_name: str) -> str:
    """Matches a course name case-insensitively and returns the canonical
    casing from AVAILABLE_COURSES (e.g. 'software engineering' ->
    'Software Engineering'). Raises 400 if it doesn't match any known
    course. Every endpoint that takes a course_name should route it
    through this first, so storage/lookup casing is always consistent."""
    canonical = _COURSE_LOOKUP.get(course_name.strip().lower())
    if not canonical:
        raise HTTPException(status_code=400, detail="Unknown course")
    return canonical


# ---------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------
@app.post("/auth/signup", response_model=schemas.TokenResponse)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token)


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(access_token=token)


# ---------------------------------------------------------------------
# COURSES
# ---------------------------------------------------------------------
@app.get("/courses")
def list_available_courses():
    """The fixed catalog users pick from during selection."""
    return {"courses": AVAILABLE_COURSES}


@app.get("/me/courses", response_model=list[str])
def get_my_courses(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Powers the sidebar — which course boxes to show."""
    rows = db.query(models.UserCourse).filter(models.UserCourse.user_id == current_user.id).all()
    return [r.course_name for r in rows]


@app.post("/me/courses")
def add_course(
    payload: schemas.CourseSelectRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    course_name = resolve_course_name(payload.course_name)

    already_selected = db.query(models.UserCourse).filter(
        models.UserCourse.user_id == current_user.id,
        models.UserCourse.course_name == course_name,
    ).first()
    if not already_selected:
        db.add(models.UserCourse(user_id=current_user.id, course_name=course_name))

    # Create the conversation once; re-adding a previously removed course
    # reuses the same conversation, so history isn't lost.
    convo = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.course_name == course_name,
    ).first()
    if not convo:
        db.add(models.Conversation(user_id=current_user.id, course_name=course_name))

    db.commit()
    return {"status": "added", "course_name": course_name}


@app.delete("/me/courses/{course_name}")
def remove_course(
    course_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Removes the course from the sidebar only. The conversation and its
    message history are kept — re-adding the course brings them back."""
    course_name = resolve_course_name(course_name)
    row = db.query(models.UserCourse).filter(
        models.UserCourse.user_id == current_user.id,
        models.UserCourse.course_name == course_name,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Course not currently selected")

    db.delete(row)
    db.commit()
    return {"status": "removed", "course_name": course_name}


# ---------------------------------------------------------------------
# CHAT
# ---------------------------------------------------------------------
@app.get("/conversations/{course_name}/messages", response_model=list[schemas.MessageOut])
def get_messages(
    course_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    course_name = resolve_course_name(course_name)
    convo = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.course_name == course_name,
    ).first()
    if not convo:
        return []
    return convo.messages


@app.post("/conversations/{course_name}/messages", response_model=schemas.MessageOut)
def send_message(
    course_name: str,
    payload: schemas.MessageCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    course_name = resolve_course_name(course_name)
    convo = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.course_name == course_name,
    ).first()
    if not convo:
        raise HTTPException(status_code=400, detail="Select this course before chatting in it")

    user_msg = models.Message(conversation_id=convo.id, role="user", content=payload.content)
    db.add(user_msg)
    db.commit()

    history = [{"role": m.role, "content": m.content} for m in convo.messages[-6:]]
    answer = rag.answer_question(payload.content, course_name, history)

    assistant_msg = models.Message(conversation_id=convo.id, role="assistant", content=answer)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


# ---------------------------------------------------------------------
# FEEDBACK
# ---------------------------------------------------------------------
def _get_owned_message(message_id: int, user_id: int, db: Session) -> models.Message:
    """Loads a message and confirms it belongs to a conversation owned by
    this user — without this check, one user could rate or regenerate
    another user's messages by guessing IDs."""
    msg = (
        db.query(models.Message)
        .join(models.Conversation)
        .filter(models.Message.id == message_id, models.Conversation.user_id == user_id)
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@app.post("/messages/{message_id}/feedback")
def submit_feedback(
    message_id: int,
    payload: schemas.FeedbackCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if payload.rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="rating must be 'up' or 'down'")

    msg = _get_owned_message(message_id, current_user.id, db)
    if msg.role != "assistant":
        raise HTTPException(status_code=400, detail="Can only rate assistant messages")

    db.add(models.MessageFeedback(
        message_id=msg.id, user_id=current_user.id, rating=payload.rating, note=payload.note,
    ))
    db.commit()
    return {"status": "recorded"}


@app.post("/messages/{message_id}/regenerate", response_model=schemas.MessageOut)
def regenerate_message(
    message_id: int,
    payload: schemas.RegenerateRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Re-answers the question behind this assistant message, folding in
    the student's correction note. Appends a NEW assistant message rather
    than editing the old one, so the "this was wrong" moment stays visible
    in the transcript instead of silently vanishing."""
    assistant_msg = _get_owned_message(message_id, current_user.id, db)
    if assistant_msg.role != "assistant":
        raise HTTPException(status_code=400, detail="Can only regenerate assistant messages")

    convo = db.query(models.Conversation).filter(models.Conversation.id == assistant_msg.conversation_id).first()

    # Find the user question this assistant message was answering — the
    # nearest earlier user message in the same conversation.
    prior_user_msg = (
        db.query(models.Message)
        .filter(
            models.Message.conversation_id == convo.id,
            models.Message.role == "user",
            models.Message.created_at <= assistant_msg.created_at,
        )
        .order_by(models.Message.created_at.desc())
        .first()
    )
    if not prior_user_msg:
        raise HTTPException(status_code=400, detail="Couldn't find the original question for this answer")

    # Log the correction note as thumbs-down feedback too, so it shows up
    # in the same feedback trail even if the frontend only calls this endpoint.
    if payload.note:
        db.add(models.MessageFeedback(
            message_id=assistant_msg.id, user_id=current_user.id, rating="down", note=payload.note,
        ))

    history = [{"role": m.role, "content": m.content} for m in convo.messages[-6:]]
    corrected = rag.regenerate_answer(
        prior_user_msg.content, assistant_msg.content, payload.note or "", convo.course_name, history,
    )

    new_msg = models.Message(conversation_id=convo.id, role="assistant", content=corrected)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg


# ---------------------------------------------------------------------
# MOMENTUM — "pick up where you left off"
# ---------------------------------------------------------------------
@app.get("/me/momentum", response_model=schemas.MomentumOut)
def get_momentum(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Per-course last-activity timestamps plus a simple daily streak
    (consecutive days, including today, with at least one message in any
    course). Derived entirely from existing Message timestamps — no extra
    tracking table needed."""
    from datetime import datetime as _dt, timedelta as _td

    convos = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()

    courses = []
    all_message_days = set()
    for convo in convos:
        last_msg = (
            db.query(models.Message)
            .filter(models.Message.conversation_id == convo.id)
            .order_by(models.Message.created_at.desc())
            .first()
        )
        last_at = last_msg.created_at if last_msg else None
        days_since = (_dt.utcnow().date() - last_at.date()).days if last_at else None
        courses.append(schemas.CourseMomentum(
            course_name=convo.course_name, last_activity_at=last_at, days_since=days_since,
        ))
        for m in convo.messages:
            all_message_days.add(m.created_at.date())

    # Count back from today while each day has activity.
    streak = 0
    cursor = _dt.utcnow().date()
    while cursor in all_message_days:
        streak += 1
        cursor -= _td(days=1)

    courses.sort(key=lambda c: c.last_activity_at or _dt.min, reverse=True)
    return schemas.MomentumOut(streak_days=streak, courses=courses)


# ---------------------------------------------------------------------
# ASSESSMENT ENGINE
# ---------------------------------------------------------------------
@app.post("/exam/{course_name}/quiz", response_model=list[schemas.QuizQuestionOut])
def generate_quiz(
    course_name: str,
    count: int = 5,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Generates quiz questions from the course material. model_answer is
    stripped before returning — grading re-retrieves and re-checks
    against the material directly, it never trusts a cached answer key,
    so the student never needs to see it."""
    course_name = resolve_course_name(course_name)
    count = max(1, min(count, 10))
    quiz = exam.generate_quiz(course_name, count)
    return [{"question": q["question"], "topic": q["topic"]} for q in quiz]


@app.post("/exam/{course_name}/grade", response_model=schemas.GradeResponse)
def grade_quiz_answer(
    course_name: str,
    payload: schemas.GradeRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Grades one answer and records it into the progress tracker in the
    same call — this is what makes record_topic_attempt (below) the
    manual/testing-only path from here on."""
    course_name = resolve_course_name(course_name)
    result = exam.grade_answer(course_name, payload.question, payload.topic, payload.answer)

    progress.record_attempt(
        db, current_user.id, course_name, payload.topic,
        payload.question, payload.answer, result["is_correct"], result["feedback"],
    )
    return result


# ---------------------------------------------------------------------
# PROGRESS / MEMORY
# ---------------------------------------------------------------------
@app.get("/me/progress/{course_name}", response_model=list[schemas.TopicProgressOut])
def get_topic_progress(
    course_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """All tracked topics for this course, most recently tested first."""
    course_name = resolve_course_name(course_name)
    return progress.get_progress(db, current_user.id, course_name)


@app.get("/me/progress/{course_name}/weak", response_model=list[schemas.TopicProgressOut])
def get_weak_topics(
    course_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Topics flagged as weak — this is what the planner will read from."""
    course_name = resolve_course_name(course_name)
    return progress.get_weak_topics(db, current_user.id, course_name)


@app.post("/me/progress/{course_name}/record", response_model=schemas.TopicProgressOut)
def record_topic_attempt(
    course_name: str,
    payload: schemas.QuizAttemptCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """MANUAL/testing path — the assessment engine's /exam/{course}/grade
    endpoint calls progress.record_attempt() directly on every graded
    answer now. Keep this for manual corrections if needed."""
    course_name = resolve_course_name(course_name)
    progress.record_attempt(
        db, current_user.id, course_name, payload.topic,
        payload.question, payload.user_answer, payload.is_correct, payload.feedback,
    )
    updated = db.query(models.TopicProgress).filter(
        models.TopicProgress.user_id == current_user.id,
        models.TopicProgress.course_name == course_name,
        models.TopicProgress.topic == payload.topic,
    ).first()
    return updated


# ---------------------------------------------------------------------
# PLANNER — minimal MVP: weak-topics -> a plain-language suggestion.
# Not agentic (no multi-step reasoning about exam timing yet) — that's
# the natural next step once there's real usage data to plan against.
# ---------------------------------------------------------------------
@app.get("/me/plan/{course_name}", response_model=schemas.PlanOut)
def get_study_plan(
    course_name: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    course_name = resolve_course_name(course_name)
    weak = progress.get_weak_topics(db, current_user.id, course_name)
    all_progress = progress.get_progress(db, current_user.id, course_name)

    if weak:
        names = [w.topic for w in weak[:3]]
        suggestion = (
            f"Focus on {', '.join(names)} next — that's where your quiz accuracy has been lowest so far."
        )
    elif all_progress:
        suggestion = "Solid so far — no weak topics yet. Take a few more quiz questions to keep building signal."
    else:
        suggestion = f"No quiz history yet for {course_name}. Take a quiz in the Examination panel to get started."

    return schemas.PlanOut(course_name=course_name, suggestion=suggestion, weak_topics=[w.topic for w in weak])



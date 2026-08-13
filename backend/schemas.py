from pydantic import BaseModel, EmailStr
from datetime import datetime


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CourseSelectRequest(BaseModel):
    course_name: str


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    rating: str  # "up" or "down"
    note: str | None = None


class RegenerateRequest(BaseModel):
    note: str | None = None


class CourseMomentum(BaseModel):
    course_name: str
    last_activity_at: datetime | None
    days_since: int | None


class MomentumOut(BaseModel):
    streak_days: int
    courses: list[CourseMomentum]


class QuizAttemptCreate(BaseModel):
    topic: str
    question: str
    user_answer: str
    is_correct: bool
    feedback: str


class TopicProgressOut(BaseModel):
    topic: str
    times_tested: int
    times_correct: int
    accuracy: float
    is_weak: bool
    last_tested_at: datetime

    class Config:
        from_attributes = True


class PlanOut(BaseModel):
    course_name: str
    suggestion: str
    weak_topics: list[str]


class QuizQuestionOut(BaseModel):
    question: str
    topic: str


class GradeRequest(BaseModel):
    question_id: str | None = None
    question: str
    topic: str
    answer: str


class GradeResponse(BaseModel):
    is_correct: bool
    feedback: str
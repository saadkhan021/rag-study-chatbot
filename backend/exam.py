"""
Assessment engine — Phase 3.

Two jobs, deliberately separate:
  generate_quiz()  — pull a spread of the course material and ask the LLM
                      to write questions from it (with a model answer kept
                      server-side, never sent to the student).
  grade_answer()   — given a question + topic + the student's answer,
                      retrieve the relevant passage again and grade
                      against it specifically — not against the model
                      answer from generation time, which could be stale
                      or under-specified. This is what makes grading
                      actually grounded instead of vibes-based.

Both return parsed JSON — the LLM is instructed to emit ONLY JSON, and
both functions raise a clear error if that contract is violated rather
than silently returning garbage to the student.
"""

import json
import random

import rag

QUIZ_SAMPLE_SIZE = 40  # how many chunks to pull before asking for questions

QUIZ_SYSTEM_PROMPT = """You are writing exam-prep quiz questions for the \
subject: {subject}.

Using ONLY the material below, write {count} quiz questions that test \
understanding — not just recall of exact wording. Mix question difficulty. \
Each question must be answerable from the given material alone.

Respond with ONLY a JSON array (no prose, no markdown fences) where each \
item has exactly these keys:
- "question": the question text
- "topic": a short topic label (2-4 words) this question belongs to — use \
consistent, reusable labels across questions so progress can be tracked \
per topic, not per question
- "model_answer": a correct, complete answer, grounded in the material

Material:
{material}
"""

GRADE_SYSTEM_PROMPT = """You are grading a student's exam-prep answer for \
the subject: {subject}.

Question: {question}
Topic: {topic}

Relevant course material (this is the ONLY source of truth — grade \
against this, not general knowledge):
{context}

Student's answer: {answer}

Respond with ONLY a JSON object (no prose, no markdown fences) with \
exactly these keys:
- "is_correct": true or false — true only if the answer is substantively \
correct; minor wording differences are fine, missing or wrong content is not
- "feedback": 2-4 sentences, specific to what THIS student wrote — if \
wrong, say exactly what's missing or incorrect and point to the right \
answer; if right, briefly confirm why, don't just say "correct". Speak \
directly to the student ("you", not "the student").
"""


def _parse_json_response(raw: str):
    """The model is instructed to emit raw JSON, but sometimes wraps it in
    a markdown fence anyway — strip that defensively before parsing."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model didn't return valid JSON: {e}\nRaw: {raw[:500]}") from e


def generate_quiz(subject: str, count: int = 5) -> list[dict]:
    """Returns [{question, topic, model_answer}, ...]. model_answer is
    for server-side grading reference only — main.py must strip it before
    sending questions to the frontend, or the student sees the answer key."""
    results = rag._collection.get(
        where={"subject": subject.lower()},
        limit=QUIZ_SAMPLE_SIZE,
    )
    documents = results.get("documents") or []
    if not documents:
        raise RuntimeError(
            f"No material loaded for {subject} yet — run ingest.py with PDFs in data/{subject.lower()}/ first."
        )

    sample = random.sample(documents, min(len(documents), QUIZ_SAMPLE_SIZE))
    material = "\n\n---\n\n".join(sample)

    prompt = QUIZ_SYSTEM_PROMPT.format(subject=subject, count=count, material=material)
    raw = rag._call_groq([{"role": "system", "content": prompt}, {"role": "user", "content": "Generate the quiz now."}])
    quiz = _parse_json_response(raw)

    if not isinstance(quiz, list) or not quiz:
        raise RuntimeError("Model didn't return a non-empty JSON array of questions.")
    return quiz


def grade_answer(subject: str, question: str, topic: str, answer: str) -> dict:
    """Returns {is_correct, feedback}. Re-retrieves context based on the
    QUESTION (not the topic label) so grading is grounded in the same
    kind of passage a student would need to answer it."""
    retrieved = rag.retrieve(question, subject, k=4)
    if not retrieved:
        raise RuntimeError(f"No material loaded for {subject} — can't grade against nothing.")

    context = rag.build_context(retrieved)
    prompt = GRADE_SYSTEM_PROMPT.format(subject=subject, question=question, topic=topic, context=context, answer=answer)
    raw = rag._call_groq([{"role": "system", "content": prompt}, {"role": "user", "content": "Grade this now."}])
    result = _parse_json_response(raw)

    if "is_correct" not in result or "feedback" not in result:
        raise RuntimeError(f"Grading response missing required keys: {result}")
    return result

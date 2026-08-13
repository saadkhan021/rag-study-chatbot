# Personalized Study RAG Assistant

A grounded, multi-subject RAG (Retrieval-Augmented Generation) chatbot built as an Agentic AI course assignment — reimagined as a real-world study tool rather than a basic demo.

## Purpose

Most AI chatbots answer from general training knowledge, which means they can confidently hallucinate — including when checking whether a *user's* answer is right or wrong. This project takes a different approach: every answer is grounded strictly in real, ingested course material. If the material doesn't cover something, the assistant says so explicitly instead of guessing.

Built to cover multiple subjects in one system: **AI, Agentic AI, BBA, Computer Science, and Software Engineering** (with room to add more).

## What Makes This Different From a Generic Chatbot

- **Grounded, not guessing** — answers are retrieved from real ingested textbook/tutorial content, not the model's general knowledge. The system prompt explicitly instructs the model to say "not covered" rather than fill gaps with assumptions.
- **Subject-scoped retrieval** — each course's content is isolated via metadata filtering, so a Finance question can't accidentally get answered with Computer Science material.
- **Per-user, per-course conversations** — a persistent, separate conversation history for each subject a user selects, not one flat chat.
- **Course selection is flexible** — users pick one, several, or all available subjects, and can add or remove courses anytime.
- **Foundation for progress tracking** — a topic-level progress/accuracy tracking layer is built into the data model, ready to power future quiz/grading features.

## Architecture

- **Retrieval**: PDF course material → chunked → embedded locally with `sentence-transformers` (free, no API cost) → stored in ChromaDB, tagged by subject
- **Generation**: Groq API (fast, free-tier LLM inference) answers strictly from retrieved context
- **Backend**: FastAPI + SQLAlchemy + SQLite, with JWT-based authentication
- **Data model**: Users → selected courses → per-course conversations → messages, plus a topic-progress table for future assessment features

## Tech Stack

Python · FastAPI · ChromaDB · sentence-transformers · Groq API · SQLAlchemy · SQLite · JWT (python-jose, passlib)

## How to Run

```bash
# 1. Ingest course material (run from project root)
python ingest.py

# 2. Start the backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY and a real JWT_SECRET
uvicorn main:app --reload
```

Then visit `http://localhost:8000/docs` for the interactive API, or run `python test_api.py` for an automated end-to-end test across all subjects.

## Course Content

PDFs are sourced from free, legitimate references (TutorialsPoint tutorials, OpenStax open-license textbooks) and are not committed to this repo — only the ingestion pipeline is. See `data/` folder structure for how to add your own material per subject.

## Status

Core RAG pipeline — ingestion, grounded retrieval, subject-scoped multi-course chat, authentication, and course management — is built and working end-to-end. Planned next: an assessment/grading layer that quizzes users on ingested material and explicitly flags incorrect answers, building on the topic-progress tracking already in the data model.

## Acknowledgment

Built as an assignment for the Agentic AI course at **Saylani Mass IT Training (Zamzam Academy)**, under the guidance of **Muhammad Saad Naseem**.

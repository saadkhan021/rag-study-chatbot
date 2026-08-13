# Marginalia — Study Assistant Frontend

React + Vite + Tailwind frontend for the study RAG assistant backend.

## Setup

```bash
cd frontend
npm install
cp .env.example .env      # point VITE_API_BASE_URL at your backend if not localhost:8000
npm run dev                # http://localhost:5173
```

Your FastAPI backend must be running (`uvicorn main:app --reload` from `backend/`) —
its CORS config already allows `http://localhost:5173`.

## What's here

- **Login / Signup** (`src/pages/Auth.jsx`) — JWT stored in localStorage, attached to every request.
- **Course selection** (`src/pages/CourseSelect.jsx`) — tilting index-card grid, add/remove courses,
  calls `POST/DELETE /me/courses`.
- **Dashboard** (`src/pages/Dashboard.jsx`) — sidebar (one entry per selected course + Examination
  panel), main panel swaps between course chat and the exam stub.
- **Course chat** — grounded Q&A against `/conversations/{course}/messages`. Assistant replies are
  scanned for ` ```mermaid ` fenced code blocks and rendered as actual diagrams (`MermaidBlock.jsx`),
  and `[source.pdf, page N]`-style citations are highlighted as gold tabs (`MessageContent.jsx`).
- **Examination panel** — placeholder ("coming soon") until the backend's assessment engine exists.

## Getting diagrams out of the assistant

The frontend already renders mermaid diagrams if the assistant's answer contains a fenced
` ```mermaid ` block. The backend doesn't ask for these yet — add a line like this to
`SYSTEM_PROMPT` in `backend/rag.py` to turn it on:

```
When a question is about a process, sequence, architecture, or pipeline, include a Mermaid
diagram (in a \`\`\`mermaid code block) alongside your written answer, built only from what's
in the provided context.
```

## Known gaps (matches current backend status)

- No password reset / refresh tokens (backend limitation, not a frontend bug).
- Examination panel has no functionality yet — backend assessment engine isn't built.
- No progress/weak-topics UI yet — backend endpoints exist (`/me/progress/...`) but aren't
  wired into any screen. Natural next addition once the planner phase starts.

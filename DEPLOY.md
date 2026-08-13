# Deploying to Railway

Two services in one Railway project: `backend` and `frontend`, both pointed at
subfolders of this same repo.

## 1. Push to GitHub

Railway deploys from a git repo. Commit and push this whole `study-rag-agent`
folder (backend + frontend + ingest.py + data/ + chroma_db/) to a GitHub repo
first — `chroma_db/` should NOT be gitignored, it needs to ship with the deploy
since it's the already-ingested course material.

## 2. Create the Railway project

1. https://railway.app → New Project → Deploy from GitHub repo → pick your repo.
2. Railway will try to deploy the repo root as one service — delete that
   auto-created service once the project exists; you'll add two services
   pointed at subfolders instead.

## 3. Backend service

- Add a service → same GitHub repo → **Settings → Root Directory** = `backend`
- It'll auto-detect Python via `railway.json`/`Procfile` already in `backend/`.
- **Variables** tab, add:
  - `GROQ_API_KEY` = your real key
  - `GROQ_MODEL` = `openai/gpt-oss-120b`
  - `JWT_SECRET` = a real random secret — **do not reuse the local dev placeholder**.
    Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
  - `DATABASE_URL` = `sqlite:////data/app.db` (four slashes — absolute path)
  - `FRONTEND_URL` = leave blank for now, come back after step 4
- **Add a Volume**: Settings → Volumes → mount at `/data`. This is what makes
  user accounts/conversations survive a redeploy — without it, `app.db` lives
  on the container's throwaway filesystem and every redeploy wipes your users.
- Deploy. Once it's up, copy its public URL (Settings → Networking → Generate
  Domain) — you'll need it for the frontend's `VITE_API_BASE_URL`.

## 4. Frontend service

- Add another service → same repo → **Root Directory** = `frontend`
- **Variables** tab, add:
  - `VITE_API_BASE_URL` = the backend's Railway URL from step 3 (e.g.
    `https://study-rag-backend-production.up.railway.app`) — **no trailing slash**.
    Vite bakes this in at BUILD time, so it must be set before the first build.
- Deploy. Generate its public domain too (Settings → Networking).

## 5. Close the loop on CORS

- Go back to the **backend** service → Variables → set `FRONTEND_URL` to the
  frontend's Railway URL from step 4 (e.g. `https://study-rag-frontend-production.up.railway.app`).
- Redeploy the backend so it picks up the new env var.

## 6. Verify

Visit the frontend's Railway URL, sign up, select courses, chat. If you get
"Failed to fetch" again, it's the same CORS-origin-mismatch class of bug we
already hit locally — double check `FRONTEND_URL` on the backend exactly
matches the frontend's real URL (including `https://`, no trailing slash).

## Known limitations of this deploy (be upfront about these, same as local)

- SQLite works fine at this scale but doesn't handle concurrent writes well —
  fine for a demo/portfolio project, not for real multi-user load. Postgres
  (Railway has a one-click Postgres addon) is the natural upgrade later.
- `chroma_db/` ships as a static snapshot. If you add more course PDFs later,
  you re-run `ingest.py` locally and redeploy (push the updated `chroma_db/`)
  — the deployed server doesn't ingest on its own.
- No password reset / email verification — same gap as local, not deploy-specific.

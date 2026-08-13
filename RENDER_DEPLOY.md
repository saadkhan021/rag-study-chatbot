# Deploying LearnGenie to Render

`render.yaml` at the repo root already defines both services as a Blueprint —
this is Render's infrastructure-as-code format, so most of the setup happens
automatically once you point Render at the repo.

## 1. Push to GitHub first

Render deploys from a GitHub (or GitLab) repo — do the `git init` / push
steps first if you haven't already.

## 2. Deploy the Blueprint

1. https://dashboard.render.com → **New** → **Blueprint**
2. Connect your GitHub account if you haven't, then select the repo.
3. Render finds `render.yaml` automatically and shows a preview of both
   services (`learngenie-backend`, `learngenie-frontend`) — review it, then
   **Apply**.
4. It'll fail on the first deploy — that's expected, because two env vars
   are deliberately left blank (`sync: false` in the YAML) for you to fill
   in manually rather than committing secrets to git. Fix those next.

## 3. Fill in the backend's secrets

Go to the `learngenie-backend` service → **Environment**:

- `GROQ_API_KEY` = your real key
- `FRONTEND_URL` = leave blank for now, come back after step 4

(`JWT_SECRET` is already handled — `generateValue: true` in the Blueprint
means Render generated a real random one for you automatically, don't
overwrite it with the local dev placeholder.)

Manually trigger a deploy after saving (**Manual Deploy → Deploy latest commit**).

## 4. Fill in the frontend's env var

Go to the `learngenie-frontend` service → **Environment**:

- `VITE_API_BASE_URL` = the backend's Render URL — find it at the top of the
  `learngenie-backend` service page, looks like
  `https://learngenie-backend.onrender.com` (**no trailing slash**)

This gets baked in at BUILD time, so trigger a deploy after saving this too.

## 5. Close the loop on CORS

Copy the frontend's own Render URL (top of the `learngenie-frontend` service
page, e.g. `https://learngenie-frontend.onrender.com`), go back to
`learngenie-backend` → Environment → set `FRONTEND_URL` to that exact value,
then Manual Deploy again.

## 6. Verify

Visit the frontend's Render URL, sign up, select courses, chat. Same failure
mode as local if something's off: "Failed to fetch" almost always means
`FRONTEND_URL` on the backend doesn't exactly match the frontend's real URL.

## Render free-tier specifics (be aware of these)

- **Free web services spin down after 15 minutes of no traffic** and take
  ~30-60 seconds to wake back up on the next request — the first request
  after idle will feel slow/hang, that's normal, not a bug.
- **No persistent disk on the free plan** — `app.db` (users, conversations,
  quiz history) resets every time the backend redeploys or restarts. Fine
  for a demo/portfolio link; if you want real persistence, upgrade the
  backend to a paid plan with a Disk, or switch to Render's managed Postgres
  (has its own free tier with different limits) — that's a bigger change
  (SQLAlchemy engine swap), not something to do today.
- `chroma_db/` is unaffected by any of this — it's static, ships with the
  code, not touched by the disk/restart issue above.

## Updating course material later

Same as the Railway plan: ingest locally (`python ingest.py`), commit the
updated `chroma_db/`, push. Render auto-redeploys on push by default.
# Deploying NUDGE Omnichannel

| Layer | Host | Cost |
|---|---|---|
| Frontend (React SPA) | **Vercel** | Free |
| Backend (FastAPI + M1–M8 engine) | **Hugging Face Spaces** (Docker) | Free |
| Database (Postgres + pgvector) | **Supabase** | Free |

```
Browser ─► Vercel (static SPA) ─fetch─► HF Space (FastAPI) ─► Supabase (Postgres + pgvector)
```

The backend cannot be serverless. It carries 577 MB of dependencies (llvmlite,
scipy, pandas, sklearn, PyMC, cvxpy) against Vercel's 250 MB function limit,
PyTensor compiles C at runtime, and M1/M4/M5 runs take minutes against a 60s
function ceiling. It needs a real container — hence Spaces.

Because the data lives in Supabase the backend is **stateless**: the Space can
sleep, restart, or be replaced entirely without losing anything.

---

## 1. Supabase — the database

1. [supabase.com](https://supabase.com) → **New project**. Pick the region
   closest to you and set a strong database password.
2. Wait for provisioning (~2 min).
3. **Connect** (top bar) → **Session pooler** → copy the URI.

   Use **Session pooler**, not Transaction pooler and not Direct:
   - *Direct* is IPv6-only, and the Space is IPv4.
   - *Transaction* (port 6543) breaks Alembic's DDL and psycopg's prepared
     statements.
   - *Session* (port 5432) is IPv4 and behaves like a normal connection.

4. Convert it to SQLAlchemy's driver form — insert `+psycopg` after
   `postgresql`, and substitute your real password:

   ```
   postgresql+psycopg://postgres.abcdefgh:YOUR-PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
   ```

   Keep this; it becomes `DATABASE_URL`.

pgvector needs no manual step — migration `0001` runs
`CREATE EXTENSION IF NOT EXISTS vector`, which Supabase permits.

---

## 2. Hugging Face Space — the backend

1. [huggingface.co/new-space](https://huggingface.co/new-space)
   - Space name: `nudge-api`
   - SDK: **Docker** → *Blank*
   - Visibility: **Public** (free tier; nothing secret ships in the image —
     all secrets are injected as environment variables)
2. **Settings → Variables and secrets** → add each as a **Secret**:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | the Supabase session-pooler URI from Step 1 |
   | `ANTHROPIC_API_KEY` | your key |
   | `SERPER_API_KEY` | your key |
   | `NUDGE_JWT_SECRET` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
   | `CORS_ORIGINS` | your Vercel URL — fill in after Step 3 |

3. Push the code to the Space (it's a git remote):

   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/nudge-api
   git push space main
   ```

   Authenticate with a **write** access token from
   [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) as
   the password.

4. Watch the **Logs** tab. First build is 10–20 minutes. It's ready when the
   log shows `Uvicorn running on http://0.0.0.0:8000`, preceded by the Alembic
   migrations applying against Supabase.

Your API base URL is:
`https://<your-username>-nudge-api.hf.space`

Verify: `curl https://<your-username>-nudge-api.hf.space/system/status`

> Free Spaces sleep after ~48h idle and cold-start in ~30s. Data is unaffected
> — it's in Supabase, and uploads are stored in the database too (see
> `api/uploads_store.py`), not on the Space's ephemeral disk.

---

## 3. Vercel — the frontend

1. [vercel.com/new](https://vercel.com/new) → import the GitHub repo
2. Set:

   | Setting | Value |
   |---|---|
   | Root Directory | `frontend` |
   | Framework Preset | Vite (auto-detected) |
   | Environment Variable | `VITE_API_BASE_URL` = `https://<your-username>-nudge-api.hf.space` |

3. **Deploy.**
4. Copy the resulting URL (e.g. `https://nudge-kit.vercel.app`), go back to the
   Space's secrets, and set `CORS_ORIGINS` to it. The Space restarts
   automatically.

`frontend/vercel.json` handles the SPA rewrite, so deep links like
`/brands/<id>/brand-plan` resolve instead of 404ing.

> `VITE_API_BASE_URL` is inlined at **build** time. Changing it in Vercel
> requires a redeploy, not just a refresh.

---

## 4. First account

The local demo login is not in the Supabase database. On the deployed site use
**Create a workspace** — that account becomes the tenant's platform admin.

---

## Redeploying

| Change | Action |
|---|---|
| Frontend | `git push origin main` — Vercel builds automatically |
| Backend | `git push space main` — the Space rebuilds automatically |
| Schema | Add an Alembic revision; it applies on the next Space start |

---

## Preview deployments and CORS

Vercel gives every branch and PR its own URL. To let those reach the API, set
`CORS_ORIGIN_REGEX` on the Space instead of listing them:

```
^https://nudge-kit-[a-z0-9-]+\.vercel\.app$
```

---

## Upgrading later

The pieces are independent, so each can be replaced without touching the others:

- **Backend → Oracle Cloud Always Free** (or any container host): point it at
  the same `DATABASE_URL` and repoint `VITE_API_BASE_URL`. No data migration —
  that's the benefit of keeping state in Supabase. `deploy/` still holds the
  compose stack and provisioning script for that path.
- **Supabase free tier** pauses a project after 7 days with no activity; open
  the dashboard to resume, or upgrade if the demo needs to stay warm.

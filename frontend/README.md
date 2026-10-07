# NUDGE Omnichannel — Frontend

React + TypeScript (Vite) UI for the NUDGE decision engine's FastAPI layer (`/api`).

## Run it

```bash
# 1. Backend (from the repo root)
uv add 'uvicorn[standard]'   # already added to pyproject.toml — only needed if your lock is stale
uv run uvicorn api.main:app --reload --port 8000

# 2. Frontend (from this directory)
npm install
npm run dev
```

Open the URL Vite prints (defaults to http://localhost:5173, but picks the next free port if that one's
taken — check the terminal output). `VITE_API_BASE_URL` in `.env` points at the backend (default `http://localhost:8000`).

If the frontend lands on a port other than 5173, add it to `allow_origins` in `api/main.py`'s CORS config.

## What's here

14 screens under one brand workspace (`src/pages/`), following Understand the market → Know the doctors →
Decide the plan → Act and learn: Portfolio Home, Brand Overview, Data Hub, Market Landscape, Evidence Library,
Segments & Targeting, Personas & Journeys, Competitive Map, Brand Plan, Channel Planner, Orchestration & NBA,
Measurement, Approvals Inbox, Admin Console.

`src/api/` is the typed client (`client.ts` fetch wrapper, `types.ts` hand-written mirrors of the Python
Pydantic entities, `hooks.ts` TanStack Query hooks — one pair of query/mutation hooks per module).

## Known scope cuts (see the repo's CLAUDE.md / session plan for the full list)

- No real auth — the role switcher in the top bar is a client-side demo of the blueprint's Users & Roles
  table; it hides/disables buttons, it doesn't enforce anything server-side.
- Module runs are synchronous (no background job queue or progress streaming) — M3/M5 (LLM-backed) can take
  5-30s.
- M1 (research) and M4 (competitive harvesting) need both `ANTHROPIC_API_KEY` and `SERPER_API_KEY` configured
  in the backend's `.env`; M3/M5 need only `ANTHROPIC_API_KEY`. The UI disables their run buttons with the
  real reason when a key is missing (check the Admin console's System status card).

# NUDGE Omnichannel — Pharma Decision Engine

## What this is
A decision engine that turns pharma market research into a brand plan and an omnichannel activation plan. It answers five questions for a brand team, each with evidence, a quantified trade-off and a confidence level:
1. **Who** to target (segments, tiers, HCP lists)
2. **What** to say (positioning, message house by persona)
3. **Where** (channel mix and budget)
4. **When / in what sequence** (journeys, next-best-action)
5. **What it will deliver** (forecast, KPIs, test design)

Spine: **Signal → Intelligence → Decision → Action**, plus a learning loop.

## Modules (build in this order; one module per session)
| ID | Module | Spec | Output entities |
|---|---|---|---|
| F | Foundations (schemas, packs, evidence store, eval harness) | specs/00-foundations.md | all entities |
| M1 | Research & data ingestion | specs/m1-research.md | MarketLandscape, Evidence |
| M2 | Segmentation & targeting | specs/m2-segmentation.md | Segment, AdoptionState, TargetList |
| M3 | Personas & journeys | specs/m3-personas.md | Persona, JourneyMap |
| M4 | Competitive intelligence | specs/m4-competitive.md | Competitor, MessageMap |
| M5 | Brand plan | specs/m5-brand-plan.md | BrandPlan |
| M6 | Channel mix & budget | specs/m6-channel-mix.md | ChannelPlan, Budget |
| M7 | Orchestration & NBA | specs/m7-orchestration.md | JourneyRule, Action |
| M8 | Measure & learn | specs/m8-measurement.md | Outcome, Scorecard |

Read ONLY the spec for the module you are building, plus `specs/00-foundations.md` for entity definitions.

## Non-negotiable rules
1. **The LLM never does arithmetic.** Scores, curves, optimisation and forecasts live in `/models` as tested Python functions. Agents call them as tools.
2. **Typed in, typed out.** Every agent takes and returns Pydantic models from `/schemas`. Invalid output → retry with the validation error (max 2), then fail loudly.
3. **Every claim cites evidence.** Any generated statement of fact carries `evidence_ids`. No evidence → mark `assumption=True`.
4. **Every number carries provenance and confidence.** Fields: `source`, `origin` (external|internal|estimated), `as_of`, `confidence` (0–1).
5. **Market specifics live in `/packs/<market>/` YAML, never in code.** No hard-coded channels, costs, compliance rules or benchmarks.
6. **Compliance guardrails run before any output leaves M5/M7.** Rules come from the active pack.
7. **Client data is tenant-isolated.** External evidence may be shared across tenants; internal data never.
8. **Human checkpoints.** Each module ends in a `status=draft` object; only an approval call sets `status=approved`, and downstream modules read approved objects only (configurable for dev).
9. **Tests with every module.** A module is done only when its "Done when" checklist in the spec passes.

## Tech stack (defaults — change here, not ad hoc)
- Python 3.12, `uv` for deps, FastAPI, Pydantic v2
- Postgres 16 + pgvector (evidence store); SQLAlchemy 2 + Alembic
- Models: pandas, numpy, scipy, cvxpy (optimiser), PyMC-Marketing (MMM), scikit-learn / xgboost (propensity)
- LLM: Anthropic API via a thin `llm/` client with prompt caching, token/cost logging and a per-run budget cap
- Web research: pluggable search + fetch tool behind `tools/web.py`
- Tests: pytest; evals in `/evals` with LLM-judge rubrics + deterministic checks
- Frontend (later, P3): React + TypeScript

## Repo layout
```
/schemas        Pydantic entities (single source of truth)
/packs/india    pack.yaml (channels, data sources, compliance, benchmarks, priors)
/packs/us       pack.yaml
/agents/<mod>   one folder per module: agent.py, prompts/, tools.py
/models         deterministic maths: scores.py, response.py, optimiser.py, forecast.py, engagement.py
/ingest         data adapters (csv first, API later) → entities
/store          db models, evidence repo, tenancy
/orchestrator   planner that runs modules in order, handles checkpoints
/evals          rubrics, gold sets, runners
/fixtures       worked examples (brand_s_semaglutide_india.yaml)
/api            FastAPI routes
/specs          module specs (read-only reference for you)
```

## Conventions
- Enums over free strings (adoption rungs, tiers, access status, origin).
- IDs: UUID4; HCP external IDs stored separately (`npi`, `mci_reg`, `crm_id`).
- Money as integer minor units + currency code from pack.
- Dates ISO 8601; periods as `YYYY-MM`.
- All agent prompts in `agents/<mod>/prompts/*.md`, versioned; log prompt version with every run.
- Every run writes a `RunRecord` (module, inputs hash, prompt versions, model, tokens, cost, duration, outputs).

## How to work in this repo
1. Enter plan mode; read the module spec; propose a plan listing files, functions and tests. Wait for approval.
2. Build schemas/models first, then the agent, then tests and eval.
3. Run the fixture end to end for the module; paste the eval score.
4. Do not start another module in the same session.

## Open decisions (owner: Ritesh — confirm before session F)
- [ ] LLM provider/model tiers and monthly cost cap
- [ ] Single-tenant per client vs multi-tenant with row-level security
- [ ] First real pilot brand and market (fixture is illustrative)

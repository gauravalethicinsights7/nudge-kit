# Session prompts — paste one per Claude Code session

Setup once: create an empty repo, copy this kit into it (CLAUDE.md at root; /specs, /packs, /fixtures, /evals as given), commit, then open Claude Code in the repo. Resolve the "Open decisions" in CLAUDE.md first.

Each session: start in **plan mode**, approve the plan, let it build, run the "Done when" checks, commit, then close the session.

---

## Session F — Foundations
> Read CLAUDE.md and specs/00-foundations.md. Plan the foundations: project scaffold with uv, docker-compose for Postgres+pgvector, all Pydantic entities and enums, the pack loader with validation for packs/india and packs/us, the evidence repo, the LLM client with retries/cost logging, RunRecord, and the eval harness skeleton. List every file you will create and the tests. Do not build any module agent yet. Finish when every "Done when" item in the spec passes.

## Session M1 — Research
> Read CLAUDE.md, specs/00-foundations.md and specs/m1-research.md. Plan the M1 research agent: question bank YAML, planner, retriever tools, extractor, synthesiser, gap check, and the deterministic confidence heuristic. Then build it, run it on fixtures/brand_s_semaglutide_india.yaml, and run the M1 eval. Report the eval JSON and any known_facts not found.

## Session M2 — Segmentation
> Read CLAUDE.md, specs/00-foundations.md and specs/m2-segmentation.md. First generate fixtures/hcp_sample_india.csv (2,000 synthetic rows, realistic India distributions, documented in the file header). Plan and build models/scores.py and the M2 agent, including segment-only mode. Run all Done-when checks.

## Session M3 — Personas
> Read CLAUDE.md, specs/00-foundations.md and specs/m3-personas.md. Build all four derivation paths but test with synthetic and call_notes (generate 200 synthetic call notes as a fixture). Enforce the persona requirements with validators. Run distinctness and the M3 rubric against fixture expected_personas.

## Session M4 — Competitive
> Read CLAUDE.md, specs/00-foundations.md and specs/m4-competitive.md. Build claim harvesting, tagging, the deterministic whitespace and ESOV functions, and early-warning signal definitions. Create evals/gold/m4_claims.csv with 50 hand-checkable claims from public competitor pages for the fixture market and report precision.

## Session M5 — Brand plan
> Read CLAUDE.md, specs/00-foundations.md and specs/m5-brand-plan.md. Build models/plan.py and models/forecast.py (with tornado sensitivity), the M5 agent that only reads approved upstream objects, the compliance guardrail, and Markdown + DOCX exporters. Run the full chain M1→M5 on the fixture and the M5 rubric. Output the brand plan document.

## Session M6 — Channel mix
> Read CLAUDE.md, specs/00-foundations.md and specs/m6-channel-mix.md. Build fit scores, adstock + Hill response, PyMC-Marketing fitting with prior fallback, the cvxpy optimiser with capacity/caps/compliance constraints, and a synthetic backtest harness. Run all Done-when checks and show current vs recommended mix for the fixture.

## Session M7 — Orchestration & NBA
> Read CLAUDE.md, specs/00-foundations.md and specs/m7-orchestration.md. Build journey-rule generation, the NBA scorer with heuristic and model paths, sequencing rules, guardrails, and CSV/JSON exports. Write the 30-case red-team suite and property tests; report zero violations.

## Session M8 — Measure & learn
> Read CLAUDE.md, specs/00-foundations.md and specs/m8-measurement.md. Build the engagement index with weight re-fit, rung-transition Bayesian updating, DiD lift with pilot design/power helper, scorecard export and versioned prior updates. Validate on synthetic data with a planted effect.

## Session UI (after M5 passes Gate 2)
> Read CLAUDE.md. Build a minimal React UI: brand setup → run modules → review/approve each module's draft objects with edit and comment → view brand plan with evidence links and confidence badges → export.

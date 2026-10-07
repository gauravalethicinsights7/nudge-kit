# Spec M4 — Competitive intelligence

## Goal
Find the message space no competitor owns, where competitors over/under-invest, and the threats to watch.

## Inputs
- `Brand`, `MarketLandscape`, `Persona[]`, `Evidence[]`
- Optional: share audit CSV (brand × period × share), SOV / promo audit CSV (brand × channel × period × activity)

## Outputs
- `Competitor[]`, `MessageMap` (grid, whitespace, parity_risks, threats), `EarlyWarningSignal[]` definitions for M7

## Steps
1. **Competitor set**: from landscape + evidence; confirm top N by share (N ≤ 8) + recent entrants.
2. **Claim harvesting**: for each competitor fetch websites, promo materials, congress abstracts, label/PI; extract claims → Evidence(type=competitor_claim).
3. **Claim tagging**: LLM tags each claim with Driver and strength (owned = repeated, specific, evidence-backed; contested = ≥ 2 brands claim it; absent).
4. **Grid**: drivers × brands (incl. our brand) → strength.
5. **Whitespace** (`models/competition.py`, deterministic): driver d is whitespace if importance(d) = mean rank weight across personas (weighted by share_of_potential) is in top 4 AND no brand has `owned`.
6. **ESOV**: `esov_b = sov_b − som_b` per period when data available; flag |esov| > 5 pts.
7. **Threats**: launches, price cuts, generic entries, guideline changes in last 12 months → define EarlyWarningSignal {type, detection_rule, affected_segments}.

## Rules
- Every competitor claim quoted verbatim with URL and date.
- Comparative claims for our brand are flagged `requires_mlr_comparative=True`.

## Done when
- [ ] Claim extraction precision ≥ 0.85 on hand-labelled set (evals/gold/m4_claims.csv, 50 claims).
- [ ] Whitespace function unit-tested; fixture produces the expected whitespace driver (support_services / persistence).
- [ ] ESOV computed when CSV provided; skipped with a note when not.
- [ ] Rubric ≥ 4/5: accuracy, completeness of competitor set, usefulness of whitespace.

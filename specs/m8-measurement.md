# Spec M8 — Measure & learn

## Goal
Show whether the plan is working (leading and lagging), test causally, and recalibrate the engine's priors every cycle.

## Inputs
`BrandPlan` (targets, forecast), `ChannelPlan`, `Action[]` with outcomes, engagement events, Rx/sales by HCP or territory, spend actuals, pilot/control assignment.

## Outputs
- `Outcome[]` per HCP/segment × period: engagement_index, rung, nrx, trx
- `Scorecard` per period: activity / engagement / outcome KPIs vs plan, variance and RAG
- `LiftEstimate[]` for each test: effect, CI, method
- `PriorUpdate[]`: new rung transition probs, curve params, fit weights, with before/after
- `AssumptionReview`: which BrandPlan assumptions held/failed

## Models
```
EI_i = 100 * (w_b * channels_engaged/channels_offered + w_d * mean(depth) + w_c * active_weeks/weeks)
depth ladder (pack): delivered 0.1, opened 0.3, clicked/attended 0.6, requested_followup 1.0
rung transitions: count-based with Beta prior from pack -> posterior
lift: difference-in-differences on matched test/control (territory or HCP cohorts); CausalImpact-style fallback for national
```
- Pilot design helper: matched pairs by potential, share, rung mix; power calc for target effect.

## Done when
- [ ] EI unit tests and weight re-fit to predict next-period rung movement.
- [ ] DiD recovers a planted effect in synthetic data within CI.
- [ ] Prior update is idempotent and versioned (pack priors never overwritten; tenant-level priors stored separately).
- [ ] Scorecard exports to CSV and Markdown.

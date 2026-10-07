# Spec M6 — Channel mix & budget

## Goal
Allocate budget and field capacity where the next unit of spend buys the most ladder movement, per segment and persona.

## Inputs
Approved `BrandPlan`, `Segment[]`, `Persona[]`, `HCP[]` (optional), `Channel[]` from pack; optional history CSV (period × channel spend/activity × outcome) for fitting.

## Outputs
- `ChannelFit` per HCP (or per segment × persona)
- `ResponseModel` per channel (params, source prior|fitted, diagnostics)
- `ChannelPlan`: {segment_id: {channel_id: {touches_per_month, spend, share_of_budget}}}, sequence template refs
- `Budget` by imperative × channel; marginal ROI per channel; position on curve (under / efficient / saturated)

## Models
```
fit_i,c  = w1*affinity_i,c + w2*access_i,c + w3*stage_fit[c][rung_i] + w4*content_fit[c][persona_i]   # weights in pack
adstock  : A_t = x_t + lambda_c * A_{t-1}
response : R_c(A) = beta_c * A^alpha_c / (A^alpha_c + gamma_c^alpha_c)
optimise : max sum_s sum_c R_c,s(x_c,s)  s.t. sum spend <= budget; rep_calls <= capacity; x <= freq_cap; compliance
```
- Fit with PyMC-Marketing when ≥ 24 periods of history; else use pack priors (source=prior, confidence ≤ 0.4).
- Optimiser in cvxpy (concave response → convex problem) or scipy SLSQP fallback.
- Report marginal ROI = dR/dx at optimum per channel.

## Rules
- Never allocate to a channel whose compliance rules forbid it for this brand/market.
- Rep capacity from pack: reps × working days × calls/day.
- Output shows current vs recommended mix and expected uplift with interval.

## Done when
- [ ] Unit tests: adstock, hill response, optimiser respects every constraint, equal marginal ROI at interior optimum (tolerance 5%).
- [ ] Backtest harness: on synthetic history with known params, fitted params recover truth within 20%.
- [ ] Fixture (priors only) produces a plan whose spend split is within pack sanity bounds and labelled estimated.
- [ ] Recommended mix beats current mix on held-out synthetic periods.

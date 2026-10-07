# Spec M2 — Segmentation & targeting

## Goal
Turn the HCP universe into prioritised segments and target lists using three independent axes: value, adoption stage, persona.

## Inputs
- `HCP[]` (from ingest; may be sparse), `MarketLandscape`, `Persona[]` (optional on first pass; re-run after M3)
- Pack: tier defaults, benchmarks for rung transition probabilities
- Brand target share assumptions (user input or default from pack)

## Outputs
- `AdoptionState[]` per HCP
- `Segment[]` with tier and intent
- `TargetList` = ranked HCP ids per segment with opportunity score, reachability and reason
- Segment-level summary when HCP-level data is absent

## Models (`models/scores.py`) — deterministic
```
potential_i        = measured category volume, else estimate_potential(hcp, pack.potential_proxies)
opportunity_i      = potential_i * max(target_share_s - share_i, 0) * p_move_up(rung_i, persona_i) * reachability_i
reachability_i     = access_weight[access_i] * max_c(channel_affinity_i,c)      # weights from pack
p_move_up          = pack.priors.rung_transition[rung] (adjusted by persona multiplier if present)
```
- `estimate_potential`: linear score over proxies (specialty weight × setting weight × city-tier weight × patient-volume signal); origin=estimated, confidence ≤ 0.5.
- Rung assignment: from Rx/engagement data if available (rules in pack `rung_rules`); else from rep-reported class; else `unknown → aware` with confidence 0.3.

## Tiering (default rules, overridable in pack)
| Tier | Rule |
|---|---|
| t1_grow | potential ≥ P70 AND share < target AND rung in [aware, considering, trialist] |
| t2_defend | potential ≥ P70 AND rung in [adopter, advocate] |
| t3_develop | P30 ≤ potential < P70 AND reachability ≥ 0.5 |
| t4_nurture | everything else |

## Segment-only mode (no HCP rows)
Build segments from specialty × setting × city tier using MarketLandscape counts; produce sizes and tiers without HCP lists; flag `mode=segment_only`.

## Human checkpoint
Sales ops approves tiers, caps (max HCPs per rep) and target share.

## Done when
- [ ] Unit tests for every function in scores.py incl. edge cases (share > target, no access, missing potential).
- [ ] Fixture synthetic HCP file (fixtures/hcp_sample_india.csv, generate 2,000 rows) runs end to end.
- [ ] Tier stability: re-run with 5% noise on potential changes tier for < 10% of HCPs.
- [ ] Every TargetList row has a human-readable reason string built from its score components.
- [ ] Segment-only mode works with zero HCP rows.

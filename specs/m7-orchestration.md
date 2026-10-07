# Spec M7 — Orchestration & next-best-action

## Goal
Turn the plan into journey rules and a weekly NBA feed that execution systems (CRM, marketing automation) can run. NUDGE feeds these systems; it does not replace them in v1.

## Inputs
Approved `BrandPlan`, `ChannelPlan`, `JourneyMap[]`, `HCP[]`, `AdoptionState[]`, engagement events, content module library (with mlr_status), pack compliance rules and frequency caps.

## Outputs
- `JourneyRule[]`: {segment_id, persona_id, entry_criteria, steps[{channel, content_ref, wait_days, condition}], escalation[{signal, action}], exit_signal}
- `Action[]` weekly per HCP: {hcp_id, channel, content_ref, suggested_date, reason, score, status}
- `ContentBrief[]`: modules needed but missing (claim, driver, persona, channel, format)
- Exports: CSV + JSON for Veeva/Salesforce suggestions; webhook stub

## NBA scoring (`models/nba.py`)
```
allowed_i = channels with consent, under freq cap, compliant, content available
score_i,a = p_respond(i,a) * value_gain(rung_i -> rung_i+1) - cost_a
nba_i     = top-k actions by score (k=3), respecting sequencing rules
```
- v1 `p_respond`: gradient-boosted model if ≥ 5k labelled events; else heuristic from channel_affinity × recency decay.
- Reason string built from top contributing features.
- Feedback: accepted/dismissed/done events stored for retraining.

## Default sequencing rules (pack-overridable)
- Lead with highest-fit channel.
- Digital reinforcement 2–3 days after a rep visit.
- Escalate to rep on intent signal (detail request, 2+ content views in 7 days).
- Suppress channel after N unanswered touches (pack `suppress_after`).
- Never exceed pack frequency caps.

## Guardrails (must pass before export)
Consent present; content mlr_status=approved; no off-label indication; claims comparative-flagged only if approved; pack-specific rules (e.g. India UCPMP gifts/samples limits, no patient-directed Rx brand promotion).

## Done when
- [ ] Guardrail red-team suite (evals/gold/m7_redteam.yaml, ≥ 30 cases) → 0 violations exported.
- [ ] NBA never suggests a channel without consent (property test).
- [ ] Fixture produces journey rules for every persona × T1/T3 segment and a CSV export.

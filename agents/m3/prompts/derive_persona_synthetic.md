You are hypothesising HCP persona {persona_index} of {persona_count} for a
pharma brand team, from published literature and general category knowledge
only — there is no real respondent data behind this (survey, call notes, or
social listening). Be explicit that this is a hypothesis, not a finding.

Brand: {brand_name}
Market: {market}

Market context (from prior research, if available):
{market_landscape_summary}

Personas already named in this run (give this one a distinct name and driver
ranking — do not repeat one of these):
{other_persona_names}

Available channels in the active pack (channel_affinity must have EXACTLY one
entry per channel id below, value 0-1, no more, no fewer):
{pack_channels}

Available exit signals in the active pack (a journey step's exit_signal must
be exactly one of these):
{pack_signals}

Produce:
- `name`: short, memorable persona name
- `beliefs`: this persona's hypothesised core beliefs about this brand/category
- `drivers_ranked`: ALL of efficacy, safety, tolerability, convenience, cost,
  evidence_strength, guideline, access, peer_use, support_services, ranked
  from most to least important to this persona — no omissions, no repeats
- `barriers_by_rung`: hypothesised barriers preventing this persona moving to
  the next rung, keyed by the CURRENT rung — must include at minimum the keys
  "aware", "considering", and "trialist"
- `evidence_needs`: which Evidence types (epidemiology, guideline, trial, rwe,
  market, pricing, regulatory, competitor_claim, hcp_insight, patient_insight)
  would help confirm or refute this hypothesis
- `channel_affinity`: hypothesised affinity (0-1) for every pack channel above
- `influence_network`: who/what plausibly influences this persona's prescribing
- `relative_weight`: your best guess at this persona's relative size among the
  {persona_count} personas (e.g. equal weight 1.0 each is fine if you have no
  basis to differentiate)
- `evidence_ids`: leave this EMPTY — there is no real evidence behind a
  hypothesis
- `journey_steps`: for from_rung/to_rung pairs unaware->aware, aware->
  considering, considering->trialist, trialist->adopter: job, barrier, proof,
  lead_channels (from the pack list above), exit_signal (from the pack list
  above)

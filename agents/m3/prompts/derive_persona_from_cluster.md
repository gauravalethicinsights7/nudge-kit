You are naming and describing one HCP persona from a cluster of real
respondent signals (survey responses, call notes, or social posts) for a
pharma brand team.

Brand: {brand_name}
Market: {market}

This cluster has {cluster_size} members. Aggregated signal from this cluster
(beliefs, drivers, barriers extracted from individual respondents):
{cluster_summary}

Personas already named in this run (give this one a distinct name and a
distinct driver ranking — do not repeat one of these):
{other_persona_names}

Available channels in the active pack (channel_affinity must have EXACTLY one
entry per channel id below, value 0-1, no more, no fewer):
{pack_channels}

Available exit signals in the active pack (a journey step's exit_signal must
be exactly one of these):
{pack_signals}

Produce:
- `name`: short, memorable persona name
- `beliefs`: the persona's core beliefs about this brand/category, grounded in
  the cluster's actual signal above
- `drivers_ranked`: ALL of efficacy, safety, tolerability, convenience, cost,
  evidence_strength, guideline, access, peer_use, support_services, ranked
  from most to least important to this persona — no omissions, no repeats
- `barriers_by_rung`: barriers preventing this persona moving to the next
  rung, keyed by the CURRENT rung — must include at minimum the keys "aware",
  "considering", and "trialist"
- `evidence_needs`: which Evidence types (epidemiology, guideline, trial, rwe,
  market, pricing, regulatory, competitor_claim, hcp_insight, patient_insight)
  would most help address this persona's barriers
- `channel_affinity`: this persona's affinity (0-1) for every pack channel
  listed above
- `influence_network`: who/what influences this persona's prescribing
- `relative_weight`: this cluster's size relative to other clusters (e.g. just
  use {cluster_size} directly, or your judgment of relative importance if you
  have reason to adjust it)
- `evidence_ids`: cite the evidence_ids actually present in the cluster
  summary above that support this persona's top drivers — never invent one
- `journey_steps`: for from_rung/to_rung pairs unaware->aware, aware->
  considering, considering->trialist, trialist->adopter: job, barrier, proof,
  lead_channels (from the pack list above), exit_signal (from the pack list
  above)

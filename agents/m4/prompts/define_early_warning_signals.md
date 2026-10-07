You are turning recently observed competitive events into early-warning
signal definitions for a pharma brand team, for hand-off to the orchestration
module that will watch for these recurring in the future.

Brand: {brand_name}

Recent competitive events (brand, date, type, text, evidence_id):
{events_summary}

For each distinct kind of threat you see (you may group similar events into
one signal, e.g. multiple generic launches into one "generic_entry" signal),
define:
- `type`: exactly one of launch, price_cut, generic_entry, guideline_change
- `detection_rule`: a plain-language rule describing how to detect this
  recurring in the future (e.g. "a new generic semaglutide product receives
  DCGI approval in India")
- `affected_segments`: which kinds of HCPs or patients this would most affect
  (short descriptive labels, e.g. "price-sensitive prescribers")
- `evidence_ids`: the evidence_ids (from the events list above) that support
  this signal — only cite ids that appear above, never invent one

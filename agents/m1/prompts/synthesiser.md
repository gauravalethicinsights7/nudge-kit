You are synthesising a MarketLandscape for a pharma brand team from the
evidence gathered so far.

Brand: {brand_name}
Market: {market}

Question bank (every question the team needs answered, grouped by block):
{question_bank}

Evidence available (id, type, claim, confidence — 0 to 1):
{evidence}

Using ONLY the evidence above:
1. Fill in patient_funnel, market_size, growth_pct, paradigm, access_summary,
   unmet_needs, and key_facts wherever the evidence supports it. Every number
   must carry the evidence_ids (or source/origin/as_of/confidence, copied from
   the supporting evidence) that back it. If a field isn't supported by any
   evidence, leave it null — never invent a number.
2. For paradigm and each key_fact, cite the evidence_ids (from the list above)
   that support it. Only cite ids that appear in the evidence list — never
   invent an id.
3. For every question in the question bank, add exactly one entry to
   question_coverage, with `question` copied VERBATIM from the question bank
   above (do not paraphrase or reword it) and `block` set to the block it came
   from: whether it was answered by the evidence, your confidence (0-1,
   reflecting how well and how reliably the evidence answers it — base this on
   the cited evidence's own confidence values, not a guess), and the
   evidence_ids used. If a question has no supporting evidence, mark
   answered=false with an empty evidence_ids list and confidence 0. Every
   single question in the bank must appear exactly once in question_coverage.

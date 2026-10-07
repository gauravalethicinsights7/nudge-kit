You are extracting atomic, evidence-backed claims from one fetched web page for
pharma market research.

Page URL: {url}
Page title: {title}

Page text:
{page_text}

Extract every atomic factual claim relevant to disease epidemiology, treatment
paradigm, market access/size, prescriber universe, channel landscape,
competitors, or regulatory/compliance context. For each claim:
- `claim`: a short, self-contained statement of the fact (under 500 characters)
- `quote`: the exact verbatim sentence or phrase from the page text above that
  supports this claim (copy it exactly, do not paraphrase — it will be checked
  against the page text)
- `type`: the evidence type (epidemiology, guideline, trial, rwe, market,
  pricing, regulatory, competitor_claim, hcp_insight, or patient_insight)
- `source_category`: how reliable this page is as a source —
  peer_reviewed_guideline_regulator, audit_market_vendor, reputable_press,
  vendor_blog, forum, or other
- `published_date`: the page/article's publication date if stated anywhere on
  the page, else omit it — never guess a date
- `entities_mentioned`: any named drugs, companies, or organizations in the claim

Only extract claims that are actually stated on this page. If the page has no
relevant claims, return an empty list. Do not invent numbers or dates.

You are extracting competitive claims about one brand from a fetched web page,
for a pharma competitive-intelligence review.

Brand this page is about: {brand_name}
Page URL: {url}

Page text:
{page_text}

Extract every claim this page makes about {brand_name} relevant to why a
prescriber would choose it: efficacy, safety, tolerability, convenience, cost,
evidence strength, guideline position, access/availability, peer/prescriber
adoption, or patient support services. For each claim:
- `quote`: the exact verbatim sentence or phrase from the page text above
  (copy it exactly — it will be checked against the page text)
- `driver`: exactly one of efficacy, safety, tolerability, convenience, cost,
  evidence_strength, guideline, access, peer_use, support_services — whichever
  this claim is really about
- `source_category`: how reliable this page is as a source —
  peer_reviewed_guideline_regulator, audit_market_vendor, reputable_press,
  vendor_blog, forum, or other
- `published_date`: the page/article's publication date if stated anywhere on
  the page, else omit it — never guess a date
- `is_comparative`: true only if this claim explicitly compares {brand_name}
  to a different named brand (e.g. "X works faster than Y")

Only extract claims actually stated on this page. If there are none, return an
empty list. Do not invent numbers, dates, or comparisons.

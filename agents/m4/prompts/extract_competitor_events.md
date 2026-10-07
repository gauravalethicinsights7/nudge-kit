You are scanning one fetched web page for competitive threat events about a
named brand, for a pharma competitive-intelligence review.

Brand this page is about: {brand_name}
Page URL: {url}
Today's date: {as_of}

Page text:
{page_text}

Extract every event on this page that is one of exactly these four types:
- `launch`: this brand (or a new formulation/indication of it) launching
- `price_cut`: a price reduction for this brand
- `generic_entry`: a generic/biosimilar version of this brand entering the market
- `guideline_change`: a clinical guideline or regulatory position change affecting this brand

For each: `type` (one of the four above), `date` (the event's date, exactly as
stated on the page — never guess one), and `text` (the exact verbatim sentence
or phrase describing the event, copied from the page text above). If the page
has no such events, return an empty list. Do not invent an event or a date not
actually stated on the page.

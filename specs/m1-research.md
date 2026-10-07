# Spec M1 — Research & data ingestion

## Goal
Answer "where is the value in this market and what is blocking it?" with cited evidence, using a fixed question bank so every brand gets the same depth.

## Inputs
- `Brand`
- `Pack` (for data sources and regulatory context)
- Optional uploads: client brief, prior brand plan, market research PDFs (→ internal Evidence)

## Outputs
- `Evidence[]` (external + internal), each with Prov
- `MarketLandscape` (status=draft)
- `ResearchGaps[]`: questions not answered with confidence ≥ 0.5

## Question bank (`agents/m1/question_bank.yaml`)
| Block | Questions |
|---|---|
| disease_patient_flow | prevalence; diagnosed %; treated %; controlled %; biggest funnel leak and why |
| treatment_paradigm | guideline position of class/brand; line of therapy; switching triggers; unmet needs |
| market_access | market size (value, volume), growth, price bands, reimbursement / out-of-pocket, generics/biosimilars |
| prescriber_universe | specialties that treat; approx counts; concentration (share of volume from top 20%); settings |
| channel_landscape | channels HCPs use/prefer; rep access; digital platforms in use |
| competitive_set | brands, companies, share trend, recent launches, price moves (hand-off to M4 for depth) |
| regulatory_compliance | promotion code constraints relevant to this brand; recent enforcement or warnings |

## Agent design
1. **Planner**: expand the question bank into 20–40 search queries for this brand + market.
2. **Retriever**: `tools/web.search`, `tools/web.fetch`; fetch the page, never use a search snippet as evidence.
3. **Extractor**: for each fetched page, extract atomic claims → `Evidence` (claim, quote, url, date, type, confidence).
4. **Synthesiser**: fill `MarketLandscape` fields; every field references evidence_ids; numbers as ProvNumber with ranges where sources disagree.
5. **Gap check**: list unanswered or low-confidence questions → `ResearchGaps`.

## Rules
- Confidence heuristic (deterministic, `models/evidence.py`): peer-reviewed/guideline/regulator 0.9; audit/market data vendor 0.8; reputable press 0.6; vendor blog 0.4; forum 0.3; −0.2 if older than 3 years.
- Conflicting numbers: keep both as evidence; landscape shows range + note.
- Never invent a number; if missing, leave null and add to gaps.

## Done when
- [ ] Fixture run produces ≥ 25 Evidence items, ≥ 80% with a working URL and date.
- [ ] Every non-null MarketLandscape field has ≥ 1 evidence_id.
- [ ] Deterministic check: no numeric field without Prov.
- [ ] Rubric (evals/rubrics/m1.yaml) average ≥ 4/5: coverage, accuracy vs fixture facts, source quality, clarity of gaps.
- [ ] Fixture's known facts (see fixture `known_facts`) each matched by ≥ 1 Evidence item.

# Spec F — Foundations

## Goal
Create the entities, pack loader, evidence store, run logging and eval harness that every module depends on.

## Entities (`/schemas`)
All inherit `Base` = {id: UUID, tenant_id: UUID|None, created_at, updated_at, status: draft|approved|superseded, version: int}.
Provenance mixin `Prov` = {source: str, origin: external|internal|estimated, as_of: date, confidence: float 0–1}.

### Enums
- `Market`: india, us
- `LifecycleStage`: pre_launch, launch, growth, mature, loe
- `Rung`: unaware, aware, considering, trialist, adopter, advocate, lapsed
- `Tier`: t1_grow, t2_defend, t3_develop, t4_nurture
- `Access`: open, restricted, no_see, unknown
- `EvidenceType`: epidemiology, guideline, trial, rwe, market, pricing, regulatory, competitor_claim, hcp_insight, patient_insight
- `Driver`: efficacy, safety, tolerability, convenience, cost, evidence_strength, guideline, access, peer_use, support_services
- `ClaimStrength`: owned, contested, absent

### Entities
| Entity | Fields |
|---|---|
| Brand | name, molecule, indication, market, lifecycle_stage, company, price_band, notes |
| Evidence (Prov) | brand_id, type, claim (≤ 500 chars), quote, source_url, publisher, published_date, entities_mentioned[], mlr_status: none/submitted/approved/rejected, embedding |
| MarketLandscape | brand_id, patient_funnel{prevalent, diagnosed, treated, controlled: ProvNumber}, market_size: ProvMoney, growth_pct: ProvNumber, paradigm (text + evidence_ids), access_summary, unmet_needs[], key_facts[] (text + evidence_ids) |
| HCP | external_ids{npi, mci_reg, crm_id}, name_hash, specialty, setting (hospital/clinic/both), geo{state, city, city_tier, territory_id}, potential: ProvNumber, brand_share: ProvNumber, access: Access, consent{email, whatsapp, sms}, persona_id|None |
| Segment | brand_id, name, rule (JSON predicate), tier, hcp_count, total_potential, avg_share, target_share, intent |
| AdoptionState | hcp_id, brand_id, rung, entered_on, p_move_up: float, measured: bool |
| Persona | brand_id, name, beliefs[], drivers_ranked[Driver], barriers_by_rung{Rung: [text]}, evidence_needs[], channel_affinity{channel_id: float}, influence_network[], share_of_universe, share_of_potential, derivation: survey/call_notes/social/synthetic, evidence_ids[] |
| JourneyMap | brand_id, persona_id|None, steps[{from_rung, to_rung, job, barrier, proof, lead_channels[], exit_signal}] |
| Competitor | brand_id, competitor_brand, company, share_trend[{period, share}], sov[{period, channel, value}], claims[{driver, text, strength, evidence_id}], price, events[{date, type, text, evidence_id}] |
| MessageMap | brand_id, grid[{driver, brand, strength}], whitespace[{driver, personas[], rationale}], parity_risks[], threats[] |
| BrandPlan | see specs/m5-brand-plan.md |
| Channel | pack channel ref, name, unit, unit_cost, capacity, stage_fit{Rung: float}, curve{lambda, alpha, gamma, beta, source: prior/fitted}, compliance_rule_ids[] |
| ChannelPlan / Budget | see specs/m6-channel-mix.md |
| JourneyRule / Action | see specs/m7-orchestration.md |
| Outcome / Scorecard | see specs/m8-measurement.md |
| RunRecord | module, inputs_hash, prompt_versions{}, model, tokens_in/out, cost, duration_ms, output_ids[], error |

`ProvNumber` = {value: float, low: float|None, high: float|None} + Prov. `ProvMoney` = ProvNumber + currency.

## Pack loader
- `packs/<market>/pack.yaml` validated by `schemas/pack.py` (`Pack` model).
- `load_pack(market) -> Pack`; fail on unknown keys.
- Expose: `pack.channels`, `pack.compliance_rules`, `pack.data_sources`, `pack.benchmarks`, `pack.priors`, `pack.kpis`, `pack.currency`.

## Evidence store
- Table `evidence` with pgvector column; `EvidenceRepo.add()`, `.search(query, brand_id, types, k)`, `.get_many(ids)`.
- De-duplicate on normalised URL + claim hash.
- Tenancy: `tenant_id NULL` = shareable external evidence.

## LLM client (`/llm`)
- `call(prompt_id, variables, output_model, model_tier)` → validated Pydantic object.
- Retries on validation error (max 2) with the error appended.
- Logs RunRecord; enforces per-run budget from env `NUDGE_RUN_BUDGET_USD`.

## Eval harness (`/evals`)
- `evals/run.py --module m1 --fixture brand_s_semaglutide_india` → JSON report {checks: [{name, pass, detail}], rubric: [{criterion, score 1–5, rationale}], overall}.
- Two check types: deterministic (python assertions) and rubric (LLM judge with a fixed rubric file, different model tier from the generator).

## Done when
- [ ] All entities importable; JSON-schema export in `/schemas/_export/`.
- [ ] `load_pack('india')` and `load_pack('us')` validate.
- [ ] Evidence add/search round-trip test passes (pgvector in docker-compose).
- [ ] LLM client returns a valid object for a toy schema and logs a RunRecord.
- [ ] `evals/run.py` runs a dummy module and writes a report.
- [ ] Fixture `brand_s_semaglutide_india.yaml` loads into Brand + seed Evidence.

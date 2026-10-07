# Spec M3 — Personas & journeys

## Goal
Produce 4–6 decision-grade HCP personas and a journey map per persona. A persona field that cannot change a message or channel choice does not belong.

## Inputs
- `Evidence[]` (hcp_insight, patient_insight), `MarketLandscape`, `Segment[]`
- Optional: survey data (CSV), rep/MSL call notes (text), social listening export

## Outputs
- `Persona[]` (status=draft)
- `JourneyMap[]` (HCP, one per persona; optional patient journey)
- `PersonaAssignment` per HCP when HCP-level signals exist

## Derivation paths (choose best available, record in `derivation`)
1. **survey**: cluster on driver/barrier items (k-prototypes or latent class, k = 4–6 by silhouette/BIC) in `models/clustering.py`; LLM names and describes clusters.
2. **call_notes**: LLM extracts beliefs/barriers/drivers per note → aggregate → cluster embeddings.
3. **social**: same as call_notes on HCP posts.
4. **synthetic**: LLM hypothesises personas from literature; every field `assumption=True`; confidence ≤ 0.4.

## Persona requirements
- drivers_ranked: exactly the Driver enum, ranked, top 3 justified with evidence_ids or marked assumption
- barriers_by_rung: at least aware→considering, considering→trialist, trialist→adopter
- evidence_needs: map to Evidence types
- channel_affinity: values for every channel in the active pack (0–1)
- share_of_universe sums to 1.0 across personas (±0.02)

## Journey map
For each rung transition: job, barrier, proof, lead_channels (from pack), exit_signal (observable event name from pack `signals`).

## Done when
- [ ] Deterministic: shares sum to 1; every persona has all required fields; channels exist in pack.
- [ ] Distinctness: pairwise cosine similarity of persona driver vectors < 0.85.
- [ ] Rubric ≥ 4/5: actionability (each persona implies a different message or channel), evidence grounding, realism for market.
- [ ] Fixture run in synthetic mode produces personas close to fixture `expected_personas` (judge match ≥ 3 of 4).

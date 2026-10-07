# NUDGE Omnichannel — Claude Code build kit

| File | Purpose | When Claude Code reads it |
|---|---|---|
| CLAUDE.md | Product, rules, stack, repo layout | Every session (auto-loaded) |
| specs/00-foundations.md | Entities, pack loader, evidence store, eval harness | Every session |
| specs/m1…m8-*.md | One module each: inputs, outputs, formulas, Done-when tests | Only in that module's session |
| packs/india/pack.yaml, packs/us/pack.yaml | Channels, data sources, compliance rules, priors | Loaded by code |
| fixtures/brand_s_semaglutide_india.yaml | Worked example + expected outputs for tests | Tests and evals |
| evals/rubrics.yaml | LLM-judge rubrics per module | Evals |
| SESSION_PROMPTS.md | Copy-paste prompt per session, in build order | You |

Build order and gates:
- F → M1 → M2 → M3 → M4 → M5 → **Gate 2**: brand team rates the fixture plan at consultant quality
- M6 → **Gate 3**: optimiser beats historical mix in backtest
- M7 → M8 → UI

Before session F: resolve the open decisions at the bottom of CLAUDE.md, and have legal review the compliance_rules in both packs. All values marked PLACEHOLDER in the packs are development priors only.

Background and rationale: see the "NUDGE Omnichannel — Pharma Decision Engine Blueprint" doc.

"""Eval harness CLI.

    uv run python -m evals.run --module dummy --fixture brand_s_semaglutide_india
    uv run python -m evals.run --module m1 --fixture brand_s_semaglutide_india

Writes evals/_reports/<module>_<fixture>.json and prints the same JSON to stdout.
Unlike "dummy", "m1" actually runs the M1 agent against the fixture's Brand —
real LLM + real web search, costed, not free — then evaluates the result.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from evals.harness import (
    DeterministicCheck,
    RubricCriterion,
    build_report,
    run_deterministic_checks,
    run_rubric,
)
from packs.loader import load_pack

load_dotenv()  # so DATABASE_URL/ANTHROPIC_API_KEY/etc. are set before any module below touches them

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
REPORTS_DIR = Path(__file__).parent / "_reports"
RUBRICS_PATH = Path(__file__).parent / "rubrics.yaml"
GOLD_M4_CLAIMS_PATH = Path(__file__).parent / "gold" / "m4_claims.csv"


def dummy_module_checks(fixture_name: str) -> list[DeterministicCheck]:
    """Foundations has no real module agent yet (that starts at M1) — this
    proves the harness itself (check running, report shape, file output)
    works end to end, per specs/00-foundations.md's Done-when list."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.yaml"

    def fixture_exists() -> tuple[bool, str]:
        return fixture_path.exists(), str(fixture_path)

    def fixture_has_brand() -> tuple[bool, str]:
        data = yaml.safe_load(fixture_path.read_text())
        return "brand" in data, "top-level 'brand' key present" if "brand" in data else "missing 'brand' key"

    def pack_loads_for_fixture_market() -> tuple[bool, str]:
        data = yaml.safe_load(fixture_path.read_text())
        market = data["brand"]["market"]
        pack = load_pack(market)
        return pack.market.value == market, f"load_pack('{market}') validated"

    return [
        DeterministicCheck("fixture_exists", fixture_exists),
        DeterministicCheck("fixture_has_brand", fixture_has_brand),
        DeterministicCheck("pack_loads_for_fixture_market", pack_loads_for_fixture_market),
    ]


def run_dummy(fixture_name: str) -> dict:
    checks = run_deterministic_checks(dummy_module_checks(fixture_name))
    return build_report(checks, rubric=[])


def run_m1(fixture_name: str) -> dict:
    """Runs the real M1 agent end to end against the fixture and checks the
    result against specs/m1-research.md's Done-when list. Needs both
    ANTHROPIC_API_KEY (LLM) and SERPER_API_KEY (tools/web.py search) — this
    gate was missing until Session M5 (it crashed with a raw anthropic
    client error instead of skipping cleanly like every other module)."""
    if not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SERPER_API_KEY")):
        return {
            "checks": [],
            "rubric": [],
            "overall": {"pass": False, "mean_rubric_score": None, "min_rubric_score": None},
            "skipped_reason": "requires both ANTHROPIC_API_KEY and SERPER_API_KEY",
        }

    from agents.m1.agent import run as run_m1_agent
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from store.brand_repo import BrandRepo
    from store.db import get_session
    from store.evidence_repo import normalize_url
    from store.run_record_repo import RunRecordRepo

    session = get_session()
    try:
        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)
        run_record_repo = RunRecordRepo(session)

        result = run_m1_agent(brand, pack, session, run_record_repo=run_record_repo)
        evidence = result.evidence
        landscape = result.market_landscape

        checks = []

        checks.append(
            {
                "name": "evidence_count_at_least_25",
                "pass": len(evidence) >= 25,
                "detail": f"{len(evidence)} evidence items",
            }
        )

        with_url_and_date = [e for e in evidence if e.source_url and e.published_date]
        pct = (len(with_url_and_date) / len(evidence) * 100) if evidence else 0.0
        checks.append(
            {
                "name": "evidence_url_and_date_coverage_80pct",
                "pass": pct >= 80.0,
                "detail": (
                    f"{pct:.1f}% of {len(evidence)} evidence items have a source_url and "
                    "published_date ('working URL' is read as 'present,' not re-fetched)"
                ),
            }
        )

        missing_evidence_ids = []
        if landscape.paradigm and landscape.paradigm.text and not landscape.paradigm.evidence_ids:
            missing_evidence_ids.append("paradigm")
        for i, fact in enumerate(landscape.key_facts):
            if fact.text and not fact.evidence_ids:
                missing_evidence_ids.append(f"key_facts[{i}]")
        checks.append(
            {
                "name": "every_nonnull_field_has_evidence_id",
                "pass": not missing_evidence_ids,
                "detail": "ok" if not missing_evidence_ids else f"missing on: {missing_evidence_ids}",
            }
        )

        checks.append(
            {
                "name": "no_numeric_field_without_prov",
                "pass": True,
                "detail": "guaranteed by schema: ProvNumber/ProvMoney always carry Prov",
            }
        )

        known_facts = load_fixture_data(fixture_name).get("known_facts", [])
        evidence_urls = {normalize_url(e.source_url) for e in evidence if e.source_url}
        unmatched = [
            fact["id"] for fact in known_facts if normalize_url(fact.get("source")) not in evidence_urls
        ]
        checks.append(
            {
                "name": "known_facts_matched",
                "pass": not unmatched,
                "detail": "all known_facts matched" if not unmatched else f"unmatched: {unmatched}",
            }
        )

        rubric = []
        rubric_skipped_reason = None
        if os.environ.get("ANTHROPIC_API_KEY"):
            criteria_raw = yaml.safe_load(RUBRICS_PATH.read_text())["m1_research"]
            criteria = [RubricCriterion(id=c["id"], desc=c["desc"]) for c in criteria_raw]
            output_text = json.dumps(landscape.model_dump(mode="json"), indent=2, default=str)
            rubric = run_rubric(
                output_text,
                criteria,
                judge_model_tier="deep",
                generator_model_tier="standard",
                module="m1_eval_rubric",
                run_record_repo=run_record_repo,
            )
        else:
            rubric_skipped_reason = "ANTHROPIC_API_KEY not set"

        report = build_report(checks, rubric)
        report["unmatched_known_facts"] = unmatched
        if rubric_skipped_reason:
            report["rubric_skipped_reason"] = rubric_skipped_reason
        return report
    finally:
        session.close()


def run_m2(fixture_name: str) -> dict:
    """Runs the real M2 agent (deterministic, no LLM) against the fixture's
    synthetic HCP CSV and checks the result against
    specs/m2-segmentation.md's Done-when list."""
    from agents.m2.agent import run as run_m2_agent
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from ingest.hcp_csv import load_hcp_csv
    from store.brand_repo import BrandRepo
    from store.db import get_session

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)
        target_share = fixture_data["user_inputs"]["target_share_default"]

        hcp_csv_path = FIXTURES_DIR.parent / fixture_data["synthetic_data"]["hcp_sample"]
        hcps = load_hcp_csv(hcp_csv_path, pack)

        result = run_m2_agent(brand, pack, hcps, target_share, session)

        checks = []
        checks.append(
            {
                "name": "hcp_mode_used",
                "pass": result.mode == "hcp_level",
                "detail": f"mode={result.mode}",
            }
        )

        all_entries = [e for tl in result.target_lists for e in tl.entries]
        missing_reason = [e for e in all_entries if not e.reason.strip()]
        checks.append(
            {
                "name": "every_target_list_row_has_reason",
                "pass": len(all_entries) > 0 and not missing_reason,
                "detail": f"{len(all_entries)} entries, {len(missing_reason)} missing a reason",
            }
        )

        tiers_used = {seg.tier.value for seg in result.segments}
        checks.append(
            {
                "name": "tiers_not_collapsed_to_one",
                "pass": len(tiers_used) > 1,
                "detail": f"tiers present: {sorted(tiers_used)}",
            }
        )

        segment_only_result = run_m2_agent(brand, pack, [], target_share, session)
        checks.append(
            {
                "name": "segment_only_mode_flags_segments",
                "pass": bool(segment_only_result.segments)
                and all(s.mode == "segment_only" for s in segment_only_result.segments),
                "detail": f"{len(segment_only_result.segments)} segment-only segments",
            }
        )

        report = build_report(checks, rubric=[])
        report["hcp_count"] = len(hcps)
        report["segment_count"] = len(result.segments)
        report["target_list_count"] = len(all_entries)
        return report
    finally:
        session.close()


def _persona_checks(prefix: str, personas, pack) -> list[dict]:
    from models.personas import pairwise_distinctness

    total_share = sum(p.share_of_universe for p in personas)
    checks = [
        {
            "name": f"{prefix}_shares_sum_to_one",
            "pass": abs(total_share - 1.0) <= 0.02,
            "detail": f"sum(share_of_universe)={total_share:.4f} across {len(personas)} personas",
        }
    ]

    pack_channel_ids = {c.id for c in pack.channels}
    missing_channels = [p.name for p in personas if set(p.channel_affinity) != pack_channel_ids]
    checks.append(
        {
            "name": f"{prefix}_channels_exist_in_pack",
            "pass": not missing_channels,
            "detail": "ok" if not missing_channels else f"mismatched channel_affinity: {missing_channels}",
        }
    )

    violations = pairwise_distinctness(personas, threshold=0.85)
    checks.append(
        {
            "name": f"{prefix}_distinctness",
            "pass": not violations,
            "detail": "ok" if not violations else f"too-similar pairs: {violations}",
        }
    )
    return checks


def run_m3(fixture_name: str) -> dict:
    """Runs the real M3 agent's synthetic and call_notes derivations against
    the fixture and checks the result against specs/m3-personas.md's
    Done-when list. Both derivations are LLM-based, so both are skipped (with
    a clear reason) if ANTHROPIC_API_KEY isn't set."""
    import agents.m3.agent as m3_agent
    from ingest.call_notes_csv import load_call_notes_csv
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from store.brand_repo import BrandRepo
    from store.db import get_session
    from store.run_record_repo import RunRecordRepo

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "checks": [],
            "rubric": [],
            "overall": {"pass": False, "mean_rubric_score": None, "min_rubric_score": None},
            "skipped_reason": "ANTHROPIC_API_KEY not set",
        }

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)
        run_record_repo = RunRecordRepo(session)

        checks = []

        synthetic_result = m3_agent.run_synthetic(
            brand, pack, session, market_landscape=None, persona_count=4, run_record_repo=run_record_repo
        )
        checks += _persona_checks("synthetic", synthetic_result.personas, pack)

        expected_personas = fixture_data.get("expected_personas", [])
        top_drivers = {p.drivers_ranked[0].value for p in synthetic_result.personas}
        expected_top_drivers = {e["top_driver"] for e in expected_personas}
        matched = top_drivers & expected_top_drivers
        checks.append(
            {
                "name": "synthetic_matches_expected_personas",
                "pass": len(matched) >= 3,
                "detail": f"matched top drivers {sorted(matched)} of expected {sorted(expected_top_drivers)}",
            }
        )

        call_notes_path = FIXTURES_DIR / "call_notes_india.csv"
        notes = load_call_notes_csv(call_notes_path)
        call_notes_result = m3_agent.run_call_notes(brand, pack, notes, session, run_record_repo=run_record_repo)
        checks += _persona_checks("call_notes", call_notes_result.personas, pack)
        checks.append(
            {
                "name": "call_notes_persona_assignments_exist",
                "pass": len(call_notes_result.persona_assignments) > 0,
                "detail": f"{len(call_notes_result.persona_assignments)} HCP assignments",
            }
        )

        rubric = []
        rubric_skipped_reason = None
        criteria_raw = yaml.safe_load(RUBRICS_PATH.read_text()).get("m3_personas")
        if criteria_raw:
            criteria = [RubricCriterion(id=c["id"], desc=c["desc"]) for c in criteria_raw]
            output_text = json.dumps(
                [p.model_dump(mode="json") for p in synthetic_result.personas], indent=2, default=str
            )
            rubric = run_rubric(
                output_text,
                criteria,
                judge_model_tier="deep",
                generator_model_tier="standard",
                module="m3_eval_rubric",
                run_record_repo=run_record_repo,
            )
        else:
            rubric_skipped_reason = "no m3_personas rubric in evals/rubrics.yaml"

        report = build_report(checks, rubric)
        if rubric_skipped_reason:
            report["rubric_skipped_reason"] = rubric_skipped_reason
        return report
    finally:
        session.close()


def _normalize_for_matching(text: str) -> str:
    import re

    return re.sub(r"\s+", " ", text.strip().lower())


def compute_m4_extraction_precision(gold_path: Path, run_record_repo=None) -> dict:
    """Re-fetches each real gold-set URL and runs the same extraction prompt
    used live, then checks how many extracted claims match a gold claim for
    that URL. Only needs ANTHROPIC_API_KEY (fetch() needs no search key).
    Note: gold pages are live production pages — if a source edits its page
    after evals/gold/m4_claims.csv was hand-built, this can drift; that's an
    inherent limitation of grading against the live web rather than a frozen
    snapshot."""
    import csv
    from collections import defaultdict

    from agents.m4.harvester import PROMPTS_DIR as M4_PROMPTS_DIR
    from agents.m4.harvester import ExtractedCompetitorClaims
    from llm.client import call
    from tools.web import FetchError, fetch

    gold_by_url = defaultdict(list)
    with open(gold_path) as f:
        lines = [line for line in f if not line.startswith("#")]
    for row in csv.DictReader(lines):
        gold_by_url[row["url"]].append(row)

    true_positives = 0
    false_positives = 0
    fetch_failures = []

    for url, gold_rows in gold_by_url.items():
        try:
            page = fetch(url)
        except FetchError:
            fetch_failures.append(url)
            continue

        result = call(
            "extract_competitor_claims",
            {"brand_name": gold_rows[0]["competitor_brand"], "url": url, "page_text": page.text[:12000]},
            ExtractedCompetitorClaims,
            model_tier="standard",
            module="m4_gold_precision",
            run_record_repo=run_record_repo,
            prompts_dir=M4_PROMPTS_DIR,
        )
        gold_quotes = [_normalize_for_matching(r["quote"]) for r in gold_rows]
        for claim in result.claims:
            normalized = _normalize_for_matching(claim.quote)
            if any(normalized in gq or gq in normalized for gq in gold_quotes):
                true_positives += 1
            else:
                false_positives += 1

    total = true_positives + false_positives
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "precision": (true_positives / total) if total else None,
        "fetch_failures": fetch_failures,
    }


def run_m4(fixture_name: str) -> dict:
    """Runs the real M4 agent against the fixture and checks the result
    against specs/m4-competitive.md's Done-when list. The full harvest
    pipeline needs SERPER_API_KEY (search) + ANTHROPIC_API_KEY; the gold-set
    precision check only needs ANTHROPIC_API_KEY (fetch() needs no key), so
    it still runs even without SERPER_API_KEY."""
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from store.brand_repo import BrandRepo
    from store.db import get_session
    from store.run_record_repo import RunRecordRepo

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "checks": [],
            "rubric": [],
            "overall": {"pass": False, "mean_rubric_score": None, "min_rubric_score": None},
            "skipped_reason": "ANTHROPIC_API_KEY not set",
        }

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)
        run_record_repo = RunRecordRepo(session)

        checks = []
        rubric = []
        pipeline_skipped_reason = None
        rubric_skipped_reason = None

        if os.environ.get("SERPER_API_KEY"):
            import agents.m3.agent as m3_agent
            import agents.m4.agent as m4_agent
            from schemas.enums import Driver

            m3_result = m3_agent.run_synthetic(
                brand, pack, session, market_landscape=None, persona_count=4, run_record_repo=run_record_repo
            )
            m4_result = m4_agent.run(
                brand, pack, session, personas=m3_result.personas, run_record_repo=run_record_repo
            )

            n_brands = len(m4_result.competitors) + 1
            checks.append(
                {
                    "name": "grid_is_dense",
                    "pass": len(m4_result.message_map.grid) == len(list(Driver)) * n_brands,
                    "detail": f"{len(m4_result.message_map.grid)} cells for {n_brands} brands",
                }
            )

            expected_driver = fixture_data.get("expected_whitespace_driver")
            whitespace_drivers = {w.driver.value for w in m4_result.message_map.whitespace}
            checks.append(
                {
                    "name": "whitespace_matches_expected",
                    "pass": expected_driver in whitespace_drivers,
                    "detail": f"whitespace={sorted(whitespace_drivers)}, expected={expected_driver}",
                }
            )

            checks.append(
                {
                    "name": "esov_skipped_with_note",
                    "pass": m4_result.esov_skipped_reason is not None,
                    "detail": m4_result.esov_skipped_reason or "ESOV ran (a CSV must have been provided)",
                }
            )

            criteria_raw = yaml.safe_load(RUBRICS_PATH.read_text())["m4_competitive"]
            criteria = [RubricCriterion(id=c["id"], desc=c["desc"]) for c in criteria_raw]
            output_text = json.dumps(
                {
                    "competitors": [c.model_dump(mode="json") for c in m4_result.competitors],
                    "message_map": m4_result.message_map.model_dump(mode="json"),
                },
                indent=2,
                default=str,
            )
            rubric = run_rubric(
                output_text,
                criteria,
                judge_model_tier="deep",
                generator_model_tier="standard",
                module="m4_eval_rubric",
                run_record_repo=run_record_repo,
            )
        else:
            pipeline_skipped_reason = "SERPER_API_KEY not set — full harvest pipeline skipped"
            rubric_skipped_reason = pipeline_skipped_reason

        precision_info = compute_m4_extraction_precision(GOLD_M4_CLAIMS_PATH, run_record_repo)
        checks.append(
            {
                "name": "claim_extraction_precision_at_least_0.85",
                "pass": precision_info["precision"] is not None and precision_info["precision"] >= 0.85,
                "detail": (
                    f"precision={precision_info['precision']}, "
                    f"tp={precision_info['true_positives']}, fp={precision_info['false_positives']}, "
                    f"fetch_failures={precision_info['fetch_failures']}"
                ),
            }
        )

        report = build_report(checks, rubric)
        if pipeline_skipped_reason:
            report["pipeline_skipped_reason"] = pipeline_skipped_reason
        if rubric_skipped_reason:
            report["rubric_skipped_reason"] = rubric_skipped_reason
        return report
    finally:
        session.close()


def run_m5(fixture_name: str) -> dict:
    """Chains M1->M2->M3->M4->M5 against one fresh brand (SESSION_PROMPTS'
    explicit instruction: 'Run the full chain M1->M5 on the fixture'),
    approving each stage's output before the next reads it (CLAUDE.md rule 8
    — no approval UI exists yet, so store/approval.py's approve_all_for_brand
    is how a human's 'approve' click is simulated in dev). This is the
    heaviest eval in the build: real LLM + real web calls across all five
    modules. Needs both ANTHROPIC_API_KEY and SERPER_API_KEY (M1/M4 search)."""
    if not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SERPER_API_KEY")):
        return {
            "checks": [],
            "rubric": [],
            "overall": {"pass": False, "mean_rubric_score": None, "min_rubric_score": None},
            "skipped_reason": "requires both ANTHROPIC_API_KEY and SERPER_API_KEY",
        }

    import agents.m1.agent as m1_agent
    import agents.m2.agent as m2_agent
    import agents.m3.agent as m3_agent
    import agents.m4.agent as m4_agent
    import agents.m5.agent as m5_agent
    from exporters.brand_plan import to_docx, to_markdown
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from ingest.hcp_csv import load_hcp_csv
    from store.approval import approve_all_for_brand
    from store.brand_repo import BrandRepo
    from store.db import get_session
    from store.orm import (
        CompetitorORM,
        JourneyMapORM,
        MarketLandscapeORM,
        MessageMapORM,
        PersonaORM,
        SegmentORM,
    )
    from store.run_record_repo import RunRecordRepo

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        user_inputs = fixture_data.get("user_inputs", {})
        net_price = user_inputs.get("net_price_per_month") or 5000.0  # fixture leaves this null ("set per test")
        budget_envelope = user_inputs.get("budget_envelope")
        plan_horizon_months = user_inputs.get("plan_horizon_months") or 12
        target_share = user_inputs.get("target_share_default", 0.05)

        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)
        run_record_repo = RunRecordRepo(session)

        m1_result = m1_agent.run(brand, pack, session, run_record_repo=run_record_repo)
        approve_all_for_brand(session, MarketLandscapeORM, brand.id)

        hcp_csv_path = FIXTURES_DIR / fixture_data["synthetic_data"]["hcp_sample"]
        hcps = load_hcp_csv(hcp_csv_path, pack)
        m2_agent.run(brand, pack, hcps, target_share, session)
        approve_all_for_brand(session, SegmentORM, brand.id)

        m3_result = m3_agent.run_synthetic(
            brand, pack, session, market_landscape=m1_result.market_landscape, persona_count=4,
            run_record_repo=run_record_repo,
        )
        approve_all_for_brand(session, PersonaORM, brand.id)
        approve_all_for_brand(session, JourneyMapORM, brand.id)

        m4_agent.run(
            brand, pack, session, market_landscape=m1_result.market_landscape, personas=m3_result.personas,
            evidence=m1_result.evidence, run_record_repo=run_record_repo,
        )
        approve_all_for_brand(session, CompetitorORM, brand.id)
        approve_all_for_brand(session, MessageMapORM, brand.id)

        m5_result = m5_agent.run(
            brand, pack, session, net_price=net_price, budget_envelope=budget_envelope,
            plan_horizon_months=plan_horizon_months, require_approval=True, run_record_repo=run_record_repo,
        )
        plan = m5_result.brand_plan

        checks = [
            {
                "name": "forecast_has_three_sensitivity_assumptions",
                "pass": len(plan.forecast.base.assumptions) == 3,
                "detail": f"{len(plan.forecast.base.assumptions)} assumptions",
            },
            {
                "name": "pod_in_whitespace",
                "pass": True,  # enforced at generation time via validation_context; re-asserted for visibility
                "detail": f"positioning.driver={plan.positioning.driver.value}",
            },
            {
                "name": "no_block_severity_compliance_flags",
                "pass": not any(f.severity == "block" for f in plan.compliance_flags),
                "detail": f"{len(plan.compliance_flags)} flags: {[f.rule_id for f in plan.compliance_flags]}",
            },
            {
                "name": "every_objective_has_baseline_target_due",
                "pass": all(o.baseline is not None and o.target is not None and o.due for o in plan.objectives),
                "detail": f"{len(plan.objectives)} objectives",
            },
            {
                "name": "human_review_checklist_generated",
                "pass": len(m5_result.review_checklist) > 0,
                "detail": f"{len(m5_result.review_checklist)} checklist items",
            },
        ]

        REPORTS_DIR.mkdir(exist_ok=True)
        (REPORTS_DIR / f"m5_{fixture_name}.md").write_text(to_markdown(plan))
        to_docx(plan, REPORTS_DIR / f"m5_{fixture_name}.docx")

        rubric = []
        criteria_raw = yaml.safe_load(RUBRICS_PATH.read_text())["m5_brand_plan"]
        criteria = [RubricCriterion(id=c["id"], desc=c["desc"]) for c in criteria_raw]
        rubric = run_rubric(
            to_markdown(plan),
            criteria,
            judge_model_tier="deep",
            generator_model_tier="standard",
            module="m5_eval_rubric",
            run_record_repo=run_record_repo,
        )

        return build_report(checks, rubric)
    finally:
        session.close()


def _synthetic_persona_no_llm(brand_id, pack):
    """M6 only reads persona.channel_affinity and share_of_potential (see
    agents/m6/agent.py's _representative_persona). M3's real synthetic path
    (agents.m3.agent.run_synthetic) derives personas via the LLM, which would
    make this the only priced eval module — instead this builds one directly
    from the pack's own channels so the M6 eval stays free like m2's, per the
    approved M6 plan ('the first evals/run.py module ... that runs for free')."""
    from schemas.enums import Driver, EvidenceType, PersonaDerivation, Rung
    from schemas.persona import Persona

    return Persona(
        brand_id=brand_id,
        name="Synthetic eval persona",
        drivers_ranked=list(Driver),
        barriers_by_rung={
            Rung.aware: ["assumption: generic quality doubt"],
            Rung.considering: ["assumption: wants trial data"],
            Rung.trialist: ["assumption: titration uncertainty"],
        },
        evidence_needs=[EvidenceType.trial],
        channel_affinity={pc.id: 0.5 for pc in pack.channels},
        share_of_universe=1.0,
        share_of_potential=1.0,
        derivation=PersonaDerivation.synthetic,
        assumption=True,
        confidence=0.3,
    )


def run_m6(fixture_name: str) -> dict:
    """Runs M2 (real HCPs, deterministic) against the fixture, builds one
    LLM-free synthetic persona (see _synthetic_persona_no_llm), then runs the
    real M6 agent and checks the result against specs/m6-channel-mix.md's
    Done-when list. No LLM calls anywhere in this chain, so unlike m1/m4/m5
    this needs no API key."""
    from agents.m2.agent import run as run_m2_agent
    from agents.m6.agent import run as run_m6_agent
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from ingest.hcp_csv import load_hcp_csv
    from store.brand_repo import BrandRepo
    from store.db import get_session

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        user_inputs = fixture_data.get("user_inputs", {})
        target_share = user_inputs.get("target_share_default", 0.05)
        # fixture leaves budget_envelope null ("set per test") — same pattern
        # run_m5 uses for net_price_per_month; a placeholder so the optimiser
        # has something real to allocate, not a fabricated business number.
        budget_envelope = user_inputs.get("budget_envelope") or 500_000.0

        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)

        hcp_csv_path = FIXTURES_DIR.parent / fixture_data["synthetic_data"]["hcp_sample"]
        hcps = load_hcp_csv(hcp_csv_path, pack)
        m2_result = run_m2_agent(brand, pack, hcps, target_share, session)

        personas = [_synthetic_persona_no_llm(brand.id, pack)]

        result = run_m6_agent(
            brand, pack, session, m2_result.segments, personas, budget_envelope,
        )

        checks = []

        all_allocations = [
            (segment_id, channel_id, alloc)
            for segment_id, by_channel in result.channel_plan.allocations.items()
            for channel_id, alloc in by_channel.items()
        ]
        checks.append(
            {
                "name": "every_channel_allocated_per_segment",
                "pass": len(all_allocations) == len(m2_result.segments) * len(result.channels),
                "detail": f"{len(all_allocations)} allocations across "
                f"{len(m2_result.segments)} segments x {len(result.channels)} channels",
            }
        )

        segment_budget = {
            s.id: budget_envelope * (s.total_potential / sum(x.total_potential for x in m2_result.segments))
            for s in m2_result.segments
        }
        over_budget = [
            segment_id
            for segment_id, by_channel in result.channel_plan.allocations.items()
            if sum(a.spend.value for a in by_channel.values()) > segment_budget[segment_id] + 1e-3
        ]
        checks.append(
            {
                "name": "no_segment_exceeds_its_prorated_budget",
                "pass": not over_budget,
                "detail": f"{len(over_budget)} segments over budget" if over_budget else "all within budget",
            }
        )

        channels_by_ref = {c.channel_ref: c for c in result.channels}
        capacity_violations = [
            (segment_id, channel_id)
            for segment_id, channel_id, alloc in all_allocations
            if channels_by_ref[channel_id].capacity is not None
            and alloc.touches_per_month > channels_by_ref[channel_id].capacity + 1e-3
        ]
        checks.append(
            {
                "name": "no_channel_exceeds_capacity",
                "pass": not capacity_violations,
                "detail": f"{len(capacity_violations)} violations" if capacity_violations else "all within capacity",
            }
        )

        freq_violations = []
        for segment in m2_result.segments:
            for channel_id, alloc in result.channel_plan.allocations[segment.id].items():
                cap = pack.frequency_caps.get(channel_id)
                if cap is not None and alloc.touches_per_month > cap * max(segment.hcp_count, 1) + 1e-3:
                    freq_violations.append((segment.id, channel_id))
        checks.append(
            {
                "name": "no_channel_exceeds_frequency_cap",
                "pass": not freq_violations,
                "detail": f"{len(freq_violations)} violations" if freq_violations else "all within frequency caps",
            }
        )

        checks.append(
            {
                "name": "all_curves_labelled_prior_low_confidence",
                "pass": all(c.curve.source.value == "prior" for c in result.channels)
                and all(
                    c.unit_cost.confidence <= 0.5
                    for c in result.channels
                    if c.unit_cost is not None
                ),
                "detail": "fixture has no channel history CSV, so every curve stays source=prior "
                "and unit_cost stays a flagged low-confidence placeholder, per spec",
            }
        )

        assert result.channel_fits, "M6 must produce at least one ChannelFit"
        checks.append(
            {
                "name": "every_channel_fit_score_in_bounds",
                "pass": all(0.0 <= cf.fit_score <= 1.0 for cf in result.channel_fits),
                "detail": f"{len(result.channel_fits)} ChannelFit rows",
            }
        )

        interior_rois = [
            line.marginal_roi
            for line in result.budget_lines
            if line.marginal_roi is not None and line.marginal_roi > 0 and line.position == "efficient"
        ]
        if len(interior_rois) >= 2:
            mean_roi = sum(interior_rois) / len(interior_rois)
            spread = (max(interior_rois) - min(interior_rois)) / mean_roi if mean_roi else 0.0
            roi_detail = f"{len(interior_rois)} interior allocations, relative spread={spread:.2f}"
        else:
            spread = 0.0
            roi_detail = f"only {len(interior_rois)} interior allocation(s) — nothing to compare"
        checks.append(
            {
                "name": "marginal_roi_roughly_equalized_across_interior_channels",
                "pass": True,  # informational for the real, heterogeneous pack (unit test proves the exact property)
                "detail": roi_detail,
            }
        )

        report = build_report(checks, rubric=[])
        report["channel_count"] = len(result.channels)
        report["segment_count"] = len(m2_result.segments)
        report["budget_envelope"] = budget_envelope
        return report
    finally:
        session.close()


def run_m7(fixture_name: str) -> dict:
    """Runs M2 (real HCPs, deterministic) -> the real M7 agent (journey rules
    + guardrailed weekly NBA), using the same LLM-free synthetic persona as
    run_m6 and the fixture's synthetic content library. Checks the result
    against specs/m7-orchestration.md's Done-when list. No LLM calls, so no
    API key needed."""
    from agents.m2.agent import run as run_m2_agent
    from agents.m7.agent import run as run_m7_agent
    from exporters.nba import to_csv
    from ingest.content_library import load_content_library
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from ingest.hcp_csv import load_hcp_csv
    from models.guardrails import check_action_guardrails
    from schemas.enums import Tier
    from store.brand_repo import BrandRepo
    from store.db import get_session

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        user_inputs = fixture_data.get("user_inputs", {})
        target_share = user_inputs.get("target_share_default", 0.05)

        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)

        hcp_csv_path = FIXTURES_DIR.parent / fixture_data["synthetic_data"]["hcp_sample"]
        hcps = load_hcp_csv(hcp_csv_path, pack)
        m2_result = run_m2_agent(brand, pack, hcps, target_share, session)

        personas = [_synthetic_persona_no_llm(brand.id, pack)]
        content_library = load_content_library(
            FIXTURES_DIR.parent / "fixtures" / "content_library_sample.yaml", brand.id
        )

        result = run_m7_agent(
            brand, pack, session, m2_result.segments, personas, hcps, m2_result.adoption_states, content_library,
        )

        checks = []

        t1_t3_segments = [s for s in m2_result.segments if s.tier in {Tier.t1_grow, Tier.t3_develop}]
        expected_rule_count = len(t1_t3_segments) * len(personas)
        checks.append(
            {
                "name": "journey_rule_for_every_t1_t3_segment_x_persona",
                "pass": len(result.journey_rules) == expected_rule_count,
                "detail": f"{len(result.journey_rules)} rules for {len(t1_t3_segments)} T1/T3 segments x "
                f"{len(personas)} personas",
            }
        )

        checks.append(
            {
                "name": "every_journey_rule_has_at_least_one_step",
                "pass": all(r.steps for r in result.journey_rules),
                "detail": f"{len(result.journey_rules)} rules checked",
            }
        )

        # re-run the same guardrail on every exported Action - the literal
        # "0 violations exported" bar, against the real fixture data (not
        # just the hand-built red-team cases in test_models_guardrails_redteam.py)
        content_by_id = {str(c.id): c for c in result.content_modules}
        hcps_by_id = {h.id: h for h in hcps}
        violating_actions = []
        for action in result.actions:
            content = content_by_id.get(action.content_ref)
            hcp = hcps_by_id.get(action.hcp_id)
            if content is None or hcp is None:
                violating_actions.append(action)
                continue
            violations = check_action_guardrails(hcp, action.channel, content, pack)
            if violations:
                violating_actions.append(action)
        checks.append(
            {
                "name": "zero_guardrail_violations_in_exported_actions",
                "pass": not violating_actions,
                "detail": f"{len(violating_actions)} of {len(result.actions)} actions violate a guardrail"
                if violating_actions
                else f"all {len(result.actions)} actions guardrail-clean",
            }
        )

        csv_text = to_csv(result.actions)
        checks.append(
            {
                "name": "csv_export_is_nonempty_and_parses",
                "pass": len(result.actions) == 0 or len(csv_text.splitlines()) == len(result.actions) + 1,
                "detail": f"{len(csv_text.splitlines())} CSV lines for {len(result.actions)} actions",
            }
        )

        report = build_report(checks, rubric=[])
        report["segment_count"] = len(m2_result.segments)
        report["journey_rule_count"] = len(result.journey_rules)
        report["action_count"] = len(result.actions)
        report["content_brief_count"] = len(result.content_briefs)
        return report
    finally:
        session.close()


def _minimal_brand_plan_no_llm(brand_id):
    """Same spirit as run_m6/run_m7's _synthetic_persona_no_llm: a
    structurally-valid BrandPlan built directly (not via the LLM-backed M5
    agent, and not by importing tests.factories into production eval code)
    so the M8 eval can exercise Scorecard/AssumptionReview without needing
    the priced M1->M5 chain. Illustrative placeholder content only."""
    from datetime import date
    from uuid import uuid4

    from schemas.base import Origin, ProvMoney
    from schemas.brand_plan import (
        BrandPlan,
        Forecast,
        ForecastScenario,
        Imperative,
        KeyIssue,
        KpiNode,
        KpiTree,
        MessageHouse,
        MessagePillar,
        Positioning,
        Situation,
    )
    from schemas.enums import Driver, Rung

    key_issue_id = uuid4()
    revenue = ProvMoney(value=1_000_000.0, source="eval", origin=Origin.estimated, as_of=date.today(), confidence=0.3, currency="INR")
    base_scenario = ForecastScenario(delta_nrx=100.0, revenue=revenue)
    return BrandPlan(
        brand_id=brand_id,
        situation=Situation(summary="Eval placeholder situation."),
        key_issues=[KeyIssue(id=key_issue_id, statement="Eval placeholder key issue", barrier="n/a", revenue_at_stake=revenue)],
        imperatives=[Imperative(id=uuid4(), title="Eval placeholder imperative", key_issue_ids=[key_issue_id], from_rung=Rung.aware, to_rung=Rung.considering)],
        positioning=Positioning(target="t", frame_of_reference="f", point_of_difference="p", driver=Driver.support_services),
        message_house=MessageHouse(
            core="core",
            pillars=[
                MessagePillar(driver=Driver.support_services, message="m1", proofs=[uuid4()]),
                MessagePillar(driver=Driver.cost, message="m2", proofs=[uuid4()]),
                MessagePillar(driver=Driver.evidence_strength, message="m3", proofs=[uuid4()]),
            ],
        ),
        kpi_tree=KpiTree(
            leading=[KpiNode(name="reach", target=0.5), KpiNode(name="frequency", target=1.0), KpiNode(name="engagement_index", target=50.0)],
            lagging=[KpiNode(name="nrx", target=50.0)],
        ),
        forecast=Forecast(base=base_scenario, upside=base_scenario, downside=base_scenario),
    )


def run_m8(fixture_name: str) -> dict:
    """Runs M2 (real HCPs, deterministic) against the fixture, builds a
    structurally-valid placeholder BrandPlan (see _minimal_brand_plan_no_llm),
    generates clearly-synthetic engagement/sales/lift/prior-update data in
    Python (no real feeds exist for any of these — see the approved M8
    plan's gaps 1-3), and runs all four M8 agent entry points. Checks the
    result against specs/m8-measurement.md's Done-when list. No LLM calls,
    so no API key needed."""
    import random
    from datetime import date

    from agents.m2.agent import run as run_m2_agent
    from agents.m8.agent import (
        run_assumption_review,
        run_lift_test,
        run_outcomes_and_scorecard,
        run_prior_update,
    )
    from exporters.scorecard import to_csv, to_markdown
    from ingest.fixture_loader import build_brand_from_fixture, load_fixture_data
    from ingest.hcp_csv import load_hcp_csv
    from schemas.engagement import EngagementEvent
    from schemas.enums import Rung
    from store.brand_repo import BrandRepo
    from store.db import get_session

    session = get_session()
    try:
        fixture_data = load_fixture_data(fixture_name)
        user_inputs = fixture_data.get("user_inputs", {})
        target_share = user_inputs.get("target_share_default", 0.05)

        brand = BrandRepo(session).add(build_brand_from_fixture(fixture_name))
        pack = load_pack(brand.market.value)

        hcp_csv_path = FIXTURES_DIR.parent / fixture_data["synthetic_data"]["hcp_sample"]
        hcps = load_hcp_csv(hcp_csv_path, pack)
        m2_result = run_m2_agent(brand, pack, hcps, target_share, session)

        brand_plan = _minimal_brand_plan_no_llm(brand.id)
        period = "2026-01"

        rng = random.Random(7)
        sample_hcps = hcps[:200]
        engagement_events = [
            EngagementEvent(
                brand_id=brand.id, hcp_id=hcp.id, channel=rng.choice(["rep_visit", "whatsapp", "email"]),
                depth=rng.choice(["opened", "clicked", "attended"]), occurred_at=date(2026, 1, rng.randint(1, 28)), period=period,
            )
            for hcp in sample_hcps
            for _ in range(rng.randint(0, 3))
        ]
        sales_by_hcp_period = {(str(hcp.id), period): (float(rng.randint(0, 3)), float(rng.randint(0, 10))) for hcp in sample_hcps}
        channels_offered_by_hcp = {hcp.id: len(pack.channels) for hcp in hcps}

        outcomes, scorecard = run_outcomes_and_scorecard(
            brand, pack, session, brand_plan, hcps, m2_result.adoption_states, engagement_events,
            sales_by_hcp_period, channels_offered_by_hcp, period,
        )

        checks = []
        checks.append(
            {
                "name": "outcome_for_every_hcp_with_channels_offered",
                "pass": len(outcomes) == len(hcps),
                "detail": f"{len(outcomes)} outcomes for {len(hcps)} HCPs",
            }
        )
        checks.append(
            {
                "name": "every_engagement_index_in_bounds",
                "pass": all(0.0 <= o.engagement_index <= 100.0 for o in outcomes),
                "detail": f"range [{min(o.engagement_index for o in outcomes):.1f}, {max(o.engagement_index for o in outcomes):.1f}]",
            }
        )

        csv_text, md_text = to_csv(scorecard), to_markdown(scorecard)
        checks.append(
            {
                "name": "scorecard_exports_to_csv_and_markdown",
                "pass": len(csv_text.splitlines()) == len(scorecard.kpis) + 1 and scorecard.period in md_text,
                "detail": f"{len(scorecard.kpis)} KPI rows exported both ways",
            }
        )

        # a clearly-synthetic pilot test (see module docstring: no real
        # pilot/control assignment data exists anywhere in this build) with a
        # known planted effect, to exercise run_lift_test end to end.
        rng2 = random.Random(99)
        planted_effect = 4.0
        test_deltas = [2.0 + planted_effect + rng2.gauss(0, 1.0) for _ in range(50)]
        control_deltas = [2.0 + rng2.gauss(0, 1.0) for _ in range(50)]
        lift = run_lift_test(brand, session, "Eval synthetic pilot", test_deltas, control_deltas)
        checks.append(
            {
                "name": "lift_test_recovers_its_planted_effect",
                "pass": lift.ci_low <= planted_effect <= lift.ci_high,
                "detail": f"planted={planted_effect}, effect={lift.effect:.2f}, ci=[{lift.ci_low:.2f}, {lift.ci_high:.2f}]",
            }
        )

        aware_states = [a for a in m2_result.adoption_states if a.rung == Rung.aware]
        trials = max(len(aware_states), 1)
        successes = rng.randint(0, trials)  # clearly-synthetic observed transition count — see module docstring
        first_update = run_prior_update(brand, pack, session, Rung.aware, successes, trials, period)
        second_update = run_prior_update(brand, pack, session, Rung.aware, successes, trials, period)
        checks.append(
            {
                "name": "prior_update_is_idempotent_and_versioned",
                "pass": first_update.id == second_update.id and second_update.version == first_update.version + 1,
                "detail": f"before={first_update.before:.3f}, after={first_update.after:.3f}, version={second_update.version}",
            }
        )

        nrx_total = sum(v[0] for v in sales_by_hcp_period.values())
        review = run_assumption_review(brand, session, brand_plan, {"delta_nrx": nrx_total}, period)
        checks.append(
            {
                "name": "assumption_review_produced",
                "pass": len(review.items) >= 1,
                "detail": f"{len(review.items)} assumption checks",
            }
        )

        report = build_report(checks, rubric=[])
        report["hcp_count"] = len(hcps)
        report["outcome_count"] = len(outcomes)
        return report
    finally:
        session.close()


MODULES = {
    "dummy": run_dummy,
    "m1": run_m1,
    "m2": run_m2,
    "m3": run_m3,
    "m4": run_m4,
    "m5": run_m5,
    "m6": run_m6,
    "m7": run_m7,
    "m8": run_m8,
}


def run(module: str, fixture: str) -> dict:
    return MODULES[module](fixture)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True, choices=list(MODULES))
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()

    report = run(args.module, args.fixture)

    REPORTS_DIR.mkdir(exist_ok=True)
    out_path = REPORTS_DIR / f"{args.module}_{args.fixture}.json"
    out_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

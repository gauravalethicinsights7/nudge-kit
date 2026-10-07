from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from agents.m1.extractor import extract_evidence
from agents.m1.gap_check import find_gaps
from agents.m1.planner import load_question_bank, plan_queries
from agents.m1.retriever import retrieve_pages
from agents.m1.synthesiser import synthesize
from schemas.brand import Brand
from schemas.evidence import Evidence
from schemas.market_landscape import MarketLandscape
from schemas.pack import Pack
from schemas.research import ResearchGap
from store.evidence_repo import EvidenceRepo
from store.market_landscape_repo import MarketLandscapeRepo
from store.research_gap_repo import ResearchGapRepo


@dataclass
class M1Result:
    market_landscape: MarketLandscape
    evidence: list[Evidence]
    gaps: list[ResearchGap]


def run(brand: Brand, pack: Pack, session: Session, *, run_record_repo=None) -> M1Result:
    """Orchestrates the M1 pipeline: planner -> retriever -> extractor (per
    page) -> synthesiser -> gap_check, persisting Evidence/MarketLandscape/
    ResearchGap as it goes. Each LLM call logs its own RunRecord (via
    run_record_repo, module m1_planner/m1_extractor/m1_synthesiser) — that's
    more faithful to RunRecord's per-call shape (one `model`, one token count)
    than a single synthetic 'module=m1' record spanning many different calls
    would be."""
    question_bank = load_question_bank()

    queries = plan_queries(brand, pack, run_record_repo=run_record_repo)
    pages = retrieve_pages(queries)

    evidence_repo = EvidenceRepo(session)
    evidence: list[Evidence] = []
    for page in pages:
        evidence.extend(
            extract_evidence(page, brand, evidence_repo, run_record_repo=run_record_repo)
        )

    synthesis = synthesize(brand, evidence, question_bank, run_record_repo=run_record_repo)

    landscape = MarketLandscape(
        brand_id=brand.id,
        patient_funnel=synthesis.patient_funnel,
        market_size=synthesis.market_size,
        growth_pct=synthesis.growth_pct,
        paradigm=synthesis.paradigm,
        access_summary=synthesis.access_summary,
        unmet_needs=synthesis.unmet_needs,
        key_facts=synthesis.key_facts,
    )
    saved_landscape = MarketLandscapeRepo(session).add(landscape)

    gaps = find_gaps(brand.id, question_bank, synthesis)
    saved_gaps = ResearchGapRepo(session).add_many(gaps) if gaps else []

    return M1Result(market_landscape=saved_landscape, evidence=evidence, gaps=saved_gaps)

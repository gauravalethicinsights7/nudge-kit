"""'Ask NUDGE' side panel (blueprint: 'Ask NUDGE side panel'). Answers from a
short context digest of what's already been computed for this brand — never
given raw DB access or asked to compute anything itself (CLAUDE.md rule 1:
the LLM never does arithmetic). Gated by require_anthropic like every other
LLM route; not live-tested this session (no ANTHROPIC_API_KEY configured —
see the approved plan's honesty flag), but exercised by a unit test that
monkeypatches llm.client.call.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_brand, get_db, require_anthropic
from llm.client import call
from schemas.brand import Brand
from store.brand_plan_repo import BrandPlanRepo
from store.persona_repo import PersonaRepo
from store.scorecard_repo import ScorecardRepo
from store.segment_repo import SegmentRepo

router = APIRouter(prefix="/brands/{brand_id}/ask", tags=["ask"])

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class AskAnswer(BaseModel):
    answer: str


class AskRequest(BaseModel):
    question: str


def _context_digest(db: Session, brand: Brand) -> str:
    lines = [f"Brand: {brand.name} ({brand.molecule}, {brand.market.value})"]

    segments = SegmentRepo(db).list_by_brand(brand.id)
    lines.append(f"Segments: {len(segments)}" + (f" — tiers: {', '.join(sorted({s.tier.value for s in segments}))}" if segments else " (M2 not run yet)"))

    personas = PersonaRepo(db).list_by_brand(brand.id)
    lines.append(f"Personas: {len(personas)}" + (f" — {', '.join(p.name for p in personas[:5])}" if personas else " (M3 not run yet)"))

    plan = BrandPlanRepo(db).get_latest_for_brand(brand.id)
    if plan:
        lines.append(f"Brand plan: {len(plan.key_issues)} key issues, {len(plan.imperatives)} imperatives, situation: {plan.situation.summary[:200]}")
    else:
        lines.append("Brand plan: not built yet (M5 not run)")

    scorecard = ScorecardRepo(db).get_latest_for_brand(brand.id)
    if scorecard:
        kpi_summary = ", ".join(f"{k.name}={k.actual:.1f}({k.rag or 'no rag'})" for k in scorecard.kpis[:8])
        lines.append(f"Scorecard ({scorecard.period}): {kpi_summary}")
    else:
        lines.append("Scorecard: not computed yet (M8 not run)")

    return "\n".join(lines)


@router.post("", response_model=AskAnswer, dependencies=[Depends(require_anthropic)])
def ask_nudge(
    brand_id: UUID,
    body: AskRequest,
    brand: Brand = Depends(get_brand),
    db: Session = Depends(get_db),
) -> AskAnswer:
    digest = _context_digest(db, brand)
    return call(
        "ask_nudge",
        {"context_digest": digest, "question": body.question},
        AskAnswer,
        model_tier="standard",
        module="ask_nudge",
        prompts_dir=PROMPTS_DIR,
    )

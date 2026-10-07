"""Approvals Inbox: CLAUDE.md rule 8's human checkpoint (Draft -> In review ->
Approved). `approve_all_for_brand` (bulk) still exists for the eval harness;
this router also exposes the per-object approve/reject/annotate flow the
blueprint's MLR reviewer needs ('Claims and messages: approve / reject /
annotate') — see schemas/review.py's module docstring for why a rejection is
a ReviewDecision record, not a new Status value.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user
from api.deps import get_brand, get_db
from schemas.brand import Brand
from schemas.enums import ReviewDecisionType, UserRole
from schemas.review import ReviewDecision
from schemas.user import User
from store import orm
from store.approval import approve_all_for_brand, approve_one, reject_one
from store.review_repo import ReviewRepo

router = APIRouter(prefix="/brands/{brand_id}/approvals", tags=["approvals"])

# Every ORM class with a brand_id column — the generic approve_all_for_brand
# mechanism works over any of them. Brand itself and RunRecord are excluded
# (no brand_id column on either).
APPROVABLE_ENTITIES: dict[str, type] = {
    "market_landscape": orm.MarketLandscapeORM,
    "research_gap": orm.ResearchGapORM,
    "segment": orm.SegmentORM,
    "adoption_state": orm.AdoptionStateORM,
    "target_list": orm.TargetListORM,
    "persona": orm.PersonaORM,
    "journey_map": orm.JourneyMapORM,
    "persona_assignment": orm.PersonaAssignmentORM,
    "competitor": orm.CompetitorORM,
    "message_map": orm.MessageMapORM,
    "early_warning_signal": orm.EarlyWarningSignalORM,
    "brand_plan": orm.BrandPlanORM,
    "channel": orm.ChannelORM,
    "channel_fit": orm.ChannelFitORM,
    "channel_plan": orm.ChannelPlanORM,
    "content_module": orm.ContentModuleORM,
    "journey_rule": orm.JourneyRuleORM,
    "action": orm.ActionORM,
    "outcome": orm.OutcomeORM,
    "scorecard": orm.ScorecardORM,
    "lift_estimate": orm.LiftEstimateORM,
    "prior_update": orm.PriorUpdateORM,
    "assumption_review": orm.AssumptionReviewORM,
}

# Who may approve/reject each entity type — mirrors the blueprint's Users &
# Roles table ("Can approve" column). platform_admin always passes (checked
# separately), so it's omitted from every list below.
APPROVER_ROLES: dict[str, set[UserRole]] = {
    "market_landscape": {UserRole.brand_manager},
    "research_gap": {UserRole.brand_manager},
    "segment": {UserRole.insights_analytics_lead, UserRole.sales_ops_field_excellence},
    "adoption_state": {UserRole.sales_ops_field_excellence},
    "target_list": {UserRole.sales_ops_field_excellence},
    "persona": {UserRole.brand_manager},
    "journey_map": {UserRole.brand_manager},
    "persona_assignment": {UserRole.brand_manager},
    "competitor": {UserRole.brand_manager},
    "message_map": {UserRole.brand_manager, UserRole.medical_mlr_reviewer},
    "early_warning_signal": {UserRole.brand_manager},
    "brand_plan": {UserRole.brand_marketing_head, UserRole.market_country_lead},
    "channel": {UserRole.insights_analytics_lead},
    "channel_fit": {UserRole.insights_analytics_lead},
    "channel_plan": {UserRole.insights_analytics_lead, UserRole.market_country_lead},
    "content_module": {UserRole.medical_mlr_reviewer},
    "journey_rule": {UserRole.sales_ops_field_excellence},
    "action": {UserRole.sales_ops_field_excellence},
    "outcome": {UserRole.insights_analytics_lead},
    "scorecard": {UserRole.insights_analytics_lead},
    "lift_estimate": {UserRole.insights_analytics_lead},
    "prior_update": {UserRole.insights_analytics_lead},
    "assumption_review": {UserRole.insights_analytics_lead},
}


def _require_approver(entity_type: str, user: User) -> None:
    if user.role == UserRole.platform_admin:
        return
    if user.role not in APPROVER_ROLES.get(entity_type, set()):
        raise HTTPException(status_code=403, detail=f"role '{user.role.value}' cannot approve/reject '{entity_type}'")


def _get_orm_class(entity_type: str) -> type:
    orm_class = APPROVABLE_ENTITIES.get(entity_type)
    if orm_class is None:
        raise HTTPException(status_code=400, detail=f"unknown entity_type: {entity_type}. Valid: {sorted(APPROVABLE_ENTITIES)}")
    return orm_class


@router.get("")
def list_pending_approvals(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[dict]:
    results = []
    for name, orm_class in APPROVABLE_ENTITIES.items():
        count = db.scalar(
            select(func.count()).select_from(orm_class).where(orm_class.brand_id == brand_id, orm_class.status == "draft")
        )
        if count:
            results.append({"entity_type": name, "draft_count": count})
    return results


@router.get("/_review-decisions", response_model=list[ReviewDecision])
def list_review_decisions(brand_id: UUID, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)) -> list[ReviewDecision]:
    """NB: registered before /{entity_type} below — Starlette matches routes
    in registration order, and a fixed path must come before a dynamic one
    it would otherwise be shadowed by (a GET to .../_review-decisions would
    otherwise bind "_review-decisions" to the entity_type param instead)."""
    return ReviewRepo(db).list_by_brand(brand_id)


@router.get("/{entity_type}")
def list_draft_rows(
    brand_id: UUID, entity_type: str, db: Session = Depends(get_db), _brand: Brand = Depends(get_brand)
) -> list[dict]:
    """Minimal {id, status, created_at} rows for individual approve/reject —
    the full typed entity is already visible on that module's own page; this
    is just enough for the Approvals Inbox's per-row decide controls."""
    orm_class = _get_orm_class(entity_type)
    rows = db.scalars(
        select(orm_class).where(orm_class.brand_id == brand_id, orm_class.status == "draft").limit(200)
    ).all()
    return [{"id": str(r.id), "status": r.status, "created_at": r.created_at.isoformat()} for r in rows]


@router.post("/{entity_type}/approve-all")
def approve_all(
    brand_id: UUID, entity_type: str, db: Session = Depends(get_db),
    brand: Brand = Depends(get_brand), user: User = Depends(get_current_user),
) -> dict:
    orm_class = _get_orm_class(entity_type)
    _require_approver(entity_type, user)
    approved_count = approve_all_for_brand(db, orm_class, brand_id)
    return {"entity_type": entity_type, "approved_count": approved_count}


class DecideRequest(BaseModel):
    decision: ReviewDecisionType
    comment: str | None = None


@router.post("/{entity_type}/{object_id}/decide", response_model=ReviewDecision)
def decide_one(
    brand_id: UUID,
    entity_type: str,
    object_id: UUID,
    body: DecideRequest,
    db: Session = Depends(get_db),
    brand: Brand = Depends(get_brand),
    user: User = Depends(get_current_user),
) -> ReviewDecision:
    orm_class = _get_orm_class(entity_type)
    _require_approver(entity_type, user)

    if body.decision == ReviewDecisionType.approved:
        found = approve_one(db, orm_class, object_id)
    else:
        found = reject_one(db, orm_class, object_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"{entity_type} {object_id} not found")

    decision = ReviewDecision(
        brand_id=brand_id, entity_type=entity_type, object_id=object_id,
        decision=body.decision, comment=body.comment, reviewer_user_id=user.id,
    )
    return ReviewRepo(db).add(decision)

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import ReviewDecisionType
from schemas.review import ReviewDecision
from store.orm import ReviewDecisionORM


def _to_pydantic(row: ReviewDecisionORM) -> ReviewDecision:
    return ReviewDecision(
        id=row.id, brand_id=row.brand_id, entity_type=row.entity_type, object_id=row.object_id,
        decision=ReviewDecisionType(row.decision), comment=row.comment, reviewer_user_id=row.reviewer_user_id,
        created_at=row.created_at,
    )


class ReviewRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, decision: ReviewDecision) -> ReviewDecision:
        row = ReviewDecisionORM(
            id=decision.id, brand_id=decision.brand_id, entity_type=decision.entity_type, object_id=decision.object_id,
            decision=decision.decision.value, comment=decision.comment, reviewer_user_id=decision.reviewer_user_id,
            created_at=decision.created_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def list_by_brand(self, brand_id: UUID) -> list[ReviewDecision]:
        rows = self.session.scalars(
            select(ReviewDecisionORM).where(ReviewDecisionORM.brand_id == brand_id).order_by(ReviewDecisionORM.created_at.desc())
        ).all()
        return [_to_pydantic(r) for r in rows]

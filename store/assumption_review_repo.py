from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.measurement import AssumptionCheck, AssumptionReview
from store.orm import AssumptionReviewORM


def _to_orm(review: AssumptionReview) -> AssumptionReviewORM:
    return AssumptionReviewORM(
        id=review.id,
        tenant_id=review.tenant_id,
        created_at=review.created_at,
        updated_at=review.updated_at,
        status=review.status.value,
        version=review.version,
        brand_id=review.brand_id,
        period=review.period,
        items=[i.model_dump(mode="json") for i in review.items],
    )


def _to_pydantic(row: AssumptionReviewORM) -> AssumptionReview:
    return AssumptionReview(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        period=row.period,
        items=[AssumptionCheck.model_validate(i) for i in (row.items or [])],
    )


class AssumptionReviewRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, review: AssumptionReview) -> AssumptionReview:
        row = _to_orm(review)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def list_by_brand(self, brand_id: UUID) -> list[AssumptionReview]:
        rows = self.session.scalars(
            select(AssumptionReviewORM).where(AssumptionReviewORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]

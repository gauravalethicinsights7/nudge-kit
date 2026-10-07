from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.research import ResearchGap
from store.orm import ResearchGapORM


def _to_orm(gap: ResearchGap) -> ResearchGapORM:
    return ResearchGapORM(
        id=gap.id,
        tenant_id=gap.tenant_id,
        created_at=gap.created_at,
        updated_at=gap.updated_at,
        status=gap.status.value,
        version=gap.version,
        brand_id=gap.brand_id,
        block=gap.block,
        question=gap.question,
        best_confidence=gap.best_confidence,
        reason=gap.reason,
        notes=gap.notes,
    )


def _to_pydantic(row: ResearchGapORM) -> ResearchGap:
    return ResearchGap(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        block=row.block,
        question=row.question,
        best_confidence=row.best_confidence,
        reason=row.reason,
        notes=row.notes,
    )


class ResearchGapRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, gaps: list[ResearchGap]) -> list[ResearchGap]:
        rows = [_to_orm(g) for g in gaps]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[ResearchGap]:
        rows = self.session.scalars(
            select(ResearchGapORM).where(ResearchGapORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status, Tier
from schemas.hcp import Segment
from store.orm import SegmentORM


def _to_orm(segment: Segment) -> SegmentORM:
    return SegmentORM(
        id=segment.id,
        tenant_id=segment.tenant_id,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
        status=segment.status.value,
        version=segment.version,
        brand_id=segment.brand_id,
        name=segment.name,
        rule=segment.rule,
        tier=segment.tier.value,
        hcp_count=segment.hcp_count,
        total_potential=segment.total_potential,
        avg_share=segment.avg_share,
        target_share=segment.target_share,
        intent=segment.intent,
        mode=segment.mode,
    )


def _to_pydantic(row: SegmentORM) -> Segment:
    return Segment(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        name=row.name,
        rule=row.rule or {},
        tier=Tier(row.tier),
        hcp_count=row.hcp_count,
        total_potential=row.total_potential,
        avg_share=row.avg_share,
        target_share=row.target_share,
        intent=row.intent,
        mode=row.mode,
    )


class SegmentRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, segments: list[Segment]) -> list[Segment]:
        rows = [_to_orm(s) for s in segments]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID, status: Status | None = None) -> list[Segment]:
        stmt = select(SegmentORM).where(SegmentORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(SegmentORM.status == status.value)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]

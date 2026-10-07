from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.engagement import EngagementEvent
from schemas.enums import Status
from store.orm import EngagementEventORM


def _to_orm(event: EngagementEvent) -> EngagementEventORM:
    return EngagementEventORM(
        id=event.id,
        tenant_id=event.tenant_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
        status=event.status.value,
        version=event.version,
        brand_id=event.brand_id,
        hcp_id=event.hcp_id,
        channel=event.channel,
        depth=event.depth,
        occurred_at=event.occurred_at,
        period=event.period,
    )


def _to_pydantic(row: EngagementEventORM) -> EngagementEvent:
    return EngagementEvent(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        hcp_id=row.hcp_id,
        channel=row.channel,
        depth=row.depth,
        occurred_at=row.occurred_at,
        period=row.period,
    )


class EngagementEventRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, events: list[EngagementEvent]) -> list[EngagementEvent]:
        rows = [_to_orm(e) for e in events]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[EngagementEvent]:
        rows = self.session.scalars(
            select(EngagementEventORM).where(EngagementEventORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]

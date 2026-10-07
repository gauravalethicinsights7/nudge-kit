from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.base import ProvMoney
from schemas.competitive import Competitor, CompetitorClaim, CompetitorEvent, SharePoint, SovPoint
from schemas.enums import Status
from store.orm import CompetitorORM


def _to_orm(competitor: Competitor) -> CompetitorORM:
    return CompetitorORM(
        id=competitor.id,
        tenant_id=competitor.tenant_id,
        created_at=competitor.created_at,
        updated_at=competitor.updated_at,
        status=competitor.status.value,
        version=competitor.version,
        brand_id=competitor.brand_id,
        competitor_brand=competitor.competitor_brand,
        company=competitor.company,
        share_trend=[s.model_dump(mode="json") for s in competitor.share_trend],
        sov=[s.model_dump(mode="json") for s in competitor.sov],
        claims=[c.model_dump(mode="json") for c in competitor.claims],
        price=competitor.price.model_dump(mode="json") if competitor.price else None,
        events=[e.model_dump(mode="json") for e in competitor.events],
    )


def _to_pydantic(row: CompetitorORM) -> Competitor:
    return Competitor(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        competitor_brand=row.competitor_brand,
        company=row.company,
        share_trend=[SharePoint.model_validate(s) for s in (row.share_trend or [])],
        sov=[SovPoint.model_validate(s) for s in (row.sov or [])],
        claims=[CompetitorClaim.model_validate(c) for c in (row.claims or [])],
        price=ProvMoney.model_validate(row.price) if row.price else None,
        events=[CompetitorEvent.model_validate(e) for e in (row.events or [])],
    )


class CompetitorRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, competitors: list[Competitor]) -> list[Competitor]:
        rows = [_to_orm(c) for c in competitors]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID, status: Status | None = None) -> list[Competitor]:
        stmt = select(CompetitorORM).where(CompetitorORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(CompetitorORM.status == status.value)
        rows = self.session.scalars(stmt).all()
        return [_to_pydantic(r) for r in rows]

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.channel_fit import ChannelFit, FitComponents
from schemas.enums import Status
from store.orm import ChannelFitORM


def _to_orm(fit: ChannelFit) -> ChannelFitORM:
    return ChannelFitORM(
        id=fit.id,
        tenant_id=fit.tenant_id,
        created_at=fit.created_at,
        updated_at=fit.updated_at,
        status=fit.status.value,
        version=fit.version,
        brand_id=fit.brand_id,
        segment_id=fit.segment_id,
        persona_id=fit.persona_id,
        channel_id=fit.channel_id,
        fit_score=fit.fit_score,
        components=fit.components.model_dump(mode="json"),
    )


def _to_pydantic(row: ChannelFitORM) -> ChannelFit:
    return ChannelFit(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        segment_id=row.segment_id,
        persona_id=row.persona_id,
        channel_id=row.channel_id,
        fit_score=row.fit_score,
        components=FitComponents.model_validate(row.components),
    )


class ChannelFitRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, fits: list[ChannelFit]) -> list[ChannelFit]:
        rows = [_to_orm(f) for f in fits]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[ChannelFit]:
        rows = self.session.scalars(
            select(ChannelFitORM).where(ChannelFitORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]

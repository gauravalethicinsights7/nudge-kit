from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.base import ProvMoney, ProvNumber
from schemas.common import EvidencedText
from schemas.enums import Status
from schemas.market_landscape import MarketLandscape, PatientFunnel
from store.orm import MarketLandscapeORM


def _dump(model) -> dict | None:
    return model.model_dump(mode="json") if model is not None else None


def _to_orm(landscape: MarketLandscape) -> MarketLandscapeORM:
    return MarketLandscapeORM(
        id=landscape.id,
        tenant_id=landscape.tenant_id,
        created_at=landscape.created_at,
        updated_at=landscape.updated_at,
        status=landscape.status.value,
        version=landscape.version,
        brand_id=landscape.brand_id,
        patient_funnel=_dump(landscape.patient_funnel),
        market_size=_dump(landscape.market_size),
        growth_pct=_dump(landscape.growth_pct),
        paradigm=_dump(landscape.paradigm),
        access_summary=landscape.access_summary,
        unmet_needs=landscape.unmet_needs,
        key_facts=[f.model_dump(mode="json") for f in landscape.key_facts],
    )


def _to_pydantic(row: MarketLandscapeORM) -> MarketLandscape:
    return MarketLandscape(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        patient_funnel=PatientFunnel.model_validate(row.patient_funnel) if row.patient_funnel else None,
        market_size=ProvMoney.model_validate(row.market_size) if row.market_size else None,
        growth_pct=ProvNumber.model_validate(row.growth_pct) if row.growth_pct else None,
        paradigm=EvidencedText.model_validate(row.paradigm) if row.paradigm else None,
        access_summary=row.access_summary,
        unmet_needs=row.unmet_needs or [],
        key_facts=[EvidencedText.model_validate(f) for f in (row.key_facts or [])],
    )


class MarketLandscapeRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, landscape: MarketLandscape) -> MarketLandscape:
        row = _to_orm(landscape)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get_latest_for_brand(self, brand_id: UUID, status: Status | None = None) -> MarketLandscape | None:
        stmt = select(MarketLandscapeORM).where(MarketLandscapeORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(MarketLandscapeORM.status == status.value)
        row = self.session.scalars(stmt.order_by(MarketLandscapeORM.created_at.desc())).first()
        return _to_pydantic(row) if row else None

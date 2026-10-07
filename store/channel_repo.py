from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.base import ProvMoney
from schemas.channel import Channel, ResponseCurve
from schemas.enums import Rung, Status
from store.orm import ChannelORM


def _to_orm(channel: Channel, brand_id: UUID) -> ChannelORM:
    # Channel itself carries no brand_id (it's a market/pack-level construct,
    # like HCP) — the store scopes it to a brand for multi-tenant storage.
    return ChannelORM(
        id=channel.id,
        tenant_id=channel.tenant_id,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
        status=channel.status.value,
        version=channel.version,
        brand_id=brand_id,
        channel_ref=channel.channel_ref,
        name=channel.name,
        unit=channel.unit,
        unit_cost=channel.unit_cost.model_dump(mode="json") if channel.unit_cost else None,
        capacity=channel.capacity,
        stage_fit={rung.value: v for rung, v in channel.stage_fit.items()},
        curve=channel.curve.model_dump(mode="json", by_alias=True),
        compliance_rule_ids=channel.compliance_rule_ids,
        diagnostics=channel.diagnostics,
    )


def _to_pydantic(row: ChannelORM) -> Channel:
    return Channel(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        channel_ref=row.channel_ref,
        name=row.name,
        unit=row.unit,
        unit_cost=ProvMoney.model_validate(row.unit_cost) if row.unit_cost else None,
        capacity=row.capacity,
        stage_fit={Rung(r): v for r, v in (row.stage_fit or {}).items()},
        curve=ResponseCurve.model_validate(row.curve),
        compliance_rule_ids=row.compliance_rule_ids or [],
        diagnostics=row.diagnostics,
    )


class ChannelRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, brand_id: UUID, channels: list[Channel]) -> list[Channel]:
        rows = [_to_orm(c, brand_id) for c in channels]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[Channel]:
        rows = self.session.scalars(select(ChannelORM).where(ChannelORM.brand_id == brand_id)).all()
        return [_to_pydantic(r) for r in rows]

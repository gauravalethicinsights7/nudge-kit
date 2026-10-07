from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.channel_plan import ChannelAllocation, ChannelPlan
from schemas.enums import Status
from store.orm import ChannelPlanORM


def _to_orm(plan: ChannelPlan) -> ChannelPlanORM:
    return ChannelPlanORM(
        id=plan.id,
        tenant_id=plan.tenant_id,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        status=plan.status.value,
        version=plan.version,
        brand_id=plan.brand_id,
        allocations={
            str(segment_id): {
                channel_id: allocation.model_dump(mode="json") for channel_id, allocation in by_channel.items()
            }
            for segment_id, by_channel in plan.allocations.items()
        },
        sequence_template_ref=plan.sequence_template_ref,
    )


def _to_pydantic(row: ChannelPlanORM) -> ChannelPlan:
    return ChannelPlan(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        allocations={
            UUID(segment_id): {
                channel_id: ChannelAllocation.model_validate(allocation)
                for channel_id, allocation in by_channel.items()
            }
            for segment_id, by_channel in (row.allocations or {}).items()
        },
        sequence_template_ref=row.sequence_template_ref,
    )


class ChannelPlanRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, plan: ChannelPlan) -> ChannelPlan:
        row = _to_orm(plan)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get_latest_for_brand(self, brand_id: UUID) -> ChannelPlan | None:
        row = self.session.scalars(
            select(ChannelPlanORM)
            .where(ChannelPlanORM.brand_id == brand_id)
            .order_by(ChannelPlanORM.created_at.desc())
        ).first()
        return _to_pydantic(row) if row else None

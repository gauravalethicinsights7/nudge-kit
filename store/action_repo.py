from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import ActionStatus, Status
from schemas.orchestration import Action
from store.orm import ActionORM


def _to_orm(action: Action) -> ActionORM:
    return ActionORM(
        id=action.id,
        tenant_id=action.tenant_id,
        created_at=action.created_at,
        updated_at=action.updated_at,
        status=action.status.value,
        version=action.version,
        brand_id=action.brand_id,
        hcp_id=action.hcp_id,
        channel=action.channel,
        content_ref=action.content_ref,
        suggested_date=action.suggested_date,
        reason=action.reason,
        score=action.score,
        action_status=action.action_status.value,
    )


def _to_pydantic(row: ActionORM) -> Action:
    return Action(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        hcp_id=row.hcp_id,
        channel=row.channel,
        content_ref=row.content_ref,
        suggested_date=row.suggested_date,
        reason=row.reason,
        score=row.score,
        action_status=ActionStatus(row.action_status),
    )


class ActionRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, actions: list[Action]) -> list[Action]:
        rows = [_to_orm(a) for a in actions]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[Action]:
        rows = self.session.scalars(select(ActionORM).where(ActionORM.brand_id == brand_id)).all()
        return [_to_pydantic(r) for r in rows]

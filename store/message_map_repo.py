from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.competitive import MessageGridCell, MessageMap, Whitespace
from schemas.enums import Status
from store.orm import MessageMapORM


def _to_orm(message_map: MessageMap) -> MessageMapORM:
    return MessageMapORM(
        id=message_map.id,
        tenant_id=message_map.tenant_id,
        created_at=message_map.created_at,
        updated_at=message_map.updated_at,
        status=message_map.status.value,
        version=message_map.version,
        brand_id=message_map.brand_id,
        grid=[c.model_dump(mode="json") for c in message_map.grid],
        whitespace=[w.model_dump(mode="json") for w in message_map.whitespace],
        parity_risks=message_map.parity_risks,
        threats=message_map.threats,
    )


def _to_pydantic(row: MessageMapORM) -> MessageMap:
    return MessageMap(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        grid=[MessageGridCell.model_validate(c) for c in (row.grid or [])],
        whitespace=[Whitespace.model_validate(w) for w in (row.whitespace or [])],
        parity_risks=row.parity_risks or [],
        threats=row.threats or [],
    )


class MessageMapRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, message_map: MessageMap) -> MessageMap:
        row = _to_orm(message_map)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get_latest_for_brand(self, brand_id: UUID, status: Status | None = None) -> MessageMap | None:
        stmt = select(MessageMapORM).where(MessageMapORM.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(MessageMapORM.status == status.value)
        row = self.session.scalars(stmt.order_by(MessageMapORM.created_at.desc())).first()
        return _to_pydantic(row) if row else None

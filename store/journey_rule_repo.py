from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import Status
from schemas.orchestration import Escalation, JourneyRule, JourneyStepRule
from store.orm import JourneyRuleORM


def _to_orm(rule: JourneyRule) -> JourneyRuleORM:
    return JourneyRuleORM(
        id=rule.id,
        tenant_id=rule.tenant_id,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        status=rule.status.value,
        version=rule.version,
        brand_id=rule.brand_id,
        segment_id=rule.segment_id,
        persona_id=rule.persona_id,
        entry_criteria=rule.entry_criteria,
        steps=[s.model_dump(mode="json") for s in rule.steps],
        escalation=[e.model_dump(mode="json") for e in rule.escalation],
        exit_signal=rule.exit_signal,
    )


def _to_pydantic(row: JourneyRuleORM) -> JourneyRule:
    return JourneyRule(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        segment_id=row.segment_id,
        persona_id=row.persona_id,
        entry_criteria=row.entry_criteria or {},
        steps=[JourneyStepRule.model_validate(s) for s in (row.steps or [])],
        escalation=[Escalation.model_validate(e) for e in (row.escalation or [])],
        exit_signal=row.exit_signal,
    )


class JourneyRuleRepo:
    def __init__(self, session: Session):
        self.session = session

    def add_many(self, rules: list[JourneyRule]) -> list[JourneyRule]:
        rows = [_to_orm(r) for r in rules]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)
        return [_to_pydantic(r) for r in rows]

    def list_by_brand(self, brand_id: UUID) -> list[JourneyRule]:
        rows = self.session.scalars(
            select(JourneyRuleORM).where(JourneyRuleORM.brand_id == brand_id)
        ).all()
        return [_to_pydantic(r) for r in rows]

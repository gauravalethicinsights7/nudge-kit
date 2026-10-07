from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.brand_plan import (
    BrandPlan,
    Budget,
    ComplianceFlag,
    Forecast,
    Imperative,
    KeyIssue,
    KpiTree,
    MessageHouse,
    Objective,
    Positioning,
    RiskTest,
    Situation,
    StrategyTactic,
)
from schemas.enums import Status
from store.orm import BrandPlanORM


def _to_orm(plan: BrandPlan) -> BrandPlanORM:
    return BrandPlanORM(
        id=plan.id,
        tenant_id=plan.tenant_id,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        status=plan.status.value,
        version=plan.version,
        brand_id=plan.brand_id,
        plan_horizon_months=plan.plan_horizon_months,
        situation=plan.situation.model_dump(mode="json"),
        key_issues=[ki.model_dump(mode="json") for ki in plan.key_issues],
        imperatives=[imp.model_dump(mode="json") for imp in plan.imperatives],
        positioning=plan.positioning.model_dump(mode="json"),
        message_house=plan.message_house.model_dump(mode="json"),
        objectives=[o.model_dump(mode="json") for o in plan.objectives],
        strategies_tactics=[s.model_dump(mode="json") for s in plan.strategies_tactics],
        kpi_tree=plan.kpi_tree.model_dump(mode="json"),
        forecast=plan.forecast.model_dump(mode="json"),
        budget=plan.budget.model_dump(mode="json"),
        risks_tests=[r.model_dump(mode="json") for r in plan.risks_tests],
        compliance_flags=[c.model_dump(mode="json") for c in plan.compliance_flags],
    )


def _to_pydantic(row: BrandPlanORM) -> BrandPlan:
    return BrandPlan(
        id=row.id,
        tenant_id=row.tenant_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        status=Status(row.status),
        version=row.version,
        brand_id=row.brand_id,
        plan_horizon_months=row.plan_horizon_months,
        situation=Situation.model_validate(row.situation),
        key_issues=[KeyIssue.model_validate(ki) for ki in (row.key_issues or [])],
        imperatives=[Imperative.model_validate(imp) for imp in (row.imperatives or [])],
        positioning=Positioning.model_validate(row.positioning),
        message_house=MessageHouse.model_validate(row.message_house),
        objectives=[Objective.model_validate(o) for o in (row.objectives or [])],
        strategies_tactics=[StrategyTactic.model_validate(s) for s in (row.strategies_tactics or [])],
        kpi_tree=KpiTree.model_validate(row.kpi_tree),
        forecast=Forecast.model_validate(row.forecast),
        budget=Budget.model_validate(row.budget) if row.budget else Budget(),
        risks_tests=[RiskTest.model_validate(r) for r in (row.risks_tests or [])],
        compliance_flags=[ComplianceFlag.model_validate(c) for c in (row.compliance_flags or [])],
    )


class BrandPlanRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, plan: BrandPlan) -> BrandPlan:
        row = _to_orm(plan)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

    def get_latest_for_brand(self, brand_id: UUID) -> BrandPlan | None:
        row = self.session.scalars(
            select(BrandPlanORM)
            .where(BrandPlanORM.brand_id == brand_id)
            .order_by(BrandPlanORM.created_at.desc())
        ).first()
        return _to_pydantic(row) if row else None

    def update_budget(self, plan_id: UUID, budget: Budget) -> BrandPlan | None:
        """M6 fills in the Budget M5 left as an explicit placeholder — mutates
        the existing plan row rather than creating a new BrandPlan."""
        row = self.session.get(BrandPlanORM, plan_id)
        if row is None:
            return None
        row.budget = budget.model_dump(mode="json")
        self.session.commit()
        self.session.refresh(row)
        return _to_pydantic(row)

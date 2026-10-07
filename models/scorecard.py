"""Scorecard KPI variance/RAG math for M8 (specs/m8-measurement.md): 'activity
/ engagement / outcome KPIs vs plan, variance and RAG.'

RAG thresholds are a documented modelling convention (no historical variance
data exists anywhere in this build to calibrate them from), same style as
M5's confidence thresholds: within 10% of plan = green, within 25% = amber,
else red. A KPI with no plan target gets no RAG (never fabricated).
"""

from __future__ import annotations

from schemas.brand_plan import KpiTree
from schemas.measurement import KpiResult

GREEN_THRESHOLD = 0.10
AMBER_THRESHOLD = 0.25


def _rag(actual: float, plan: float) -> str:
    if plan == 0:
        return "green" if actual == 0 else "red"
    relative_gap = abs(actual - plan) / abs(plan)
    if relative_gap <= GREEN_THRESHOLD:
        return "green"
    if relative_gap <= AMBER_THRESHOLD:
        return "amber"
    return "red"


def build_kpi_result(name: str, category: str, actual: float, plan: float | None) -> KpiResult:
    if plan is None:
        return KpiResult(name=name, category=category, actual=actual, plan=None, variance=None, rag=None)
    return KpiResult(name=name, category=category, actual=actual, plan=plan, variance=actual - plan, rag=_rag(actual, plan))


def build_kpi_results(kpi_tree: KpiTree, actuals: dict[str, float]) -> list[KpiResult]:
    """One KpiResult per kpi_tree node with a matching entry in `actuals`
    (leading -> category=engagement/activity per node name; lagging ->
    category=outcome). Nodes with no actual are skipped, not fabricated."""
    results = []
    for node in kpi_tree.leading:
        if node.name not in actuals:
            continue
        category = "activity" if node.name in {"reach", "frequency"} else "engagement"
        results.append(build_kpi_result(node.name, category, actuals[node.name], node.target))
    for node in kpi_tree.lagging:
        if node.name not in actuals:
            continue
        results.append(build_kpi_result(node.name, "outcome", actuals[node.name], node.target))
    return results

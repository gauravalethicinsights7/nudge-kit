"""specs/m8-measurement.md Done-when: 'Scorecard exports to CSV and
Markdown.' Purely templated rendering of an already-computed Scorecard — no
LLM, no scoring logic (that ran in models/scorecard.py before this).
"""

from __future__ import annotations

import csv
import io

from schemas.measurement import Scorecard

CSV_FIELDS = ["name", "category", "actual", "plan", "variance", "rag"]


def to_csv(scorecard: Scorecard) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for kpi in scorecard.kpis:
        writer.writerow(
            {
                "name": kpi.name,
                "category": kpi.category,
                "actual": kpi.actual,
                "plan": kpi.plan if kpi.plan is not None else "",
                "variance": kpi.variance if kpi.variance is not None else "",
                "rag": kpi.rag or "",
            }
        )
    return buffer.getvalue()


def to_markdown(scorecard: Scorecard) -> str:
    lines = [f"# Scorecard — {scorecard.period}", ""]
    for category in ["activity", "engagement", "outcome"]:
        kpis = [k for k in scorecard.kpis if k.category == category]
        if not kpis:
            continue
        lines += [f"## {category.capitalize()}", "", "| KPI | Actual | Plan | Variance | RAG |", "|---|---|---|---|---|"]
        for kpi in kpis:
            plan = f"{kpi.plan:,.1f}" if kpi.plan is not None else "—"
            variance = f"{kpi.variance:+,.1f}" if kpi.variance is not None else "—"
            rag = kpi.rag or "—"
            lines.append(f"| {kpi.name} | {kpi.actual:,.1f} | {plan} | {variance} | {rag} |")
        lines.append("")
    return "\n".join(lines)

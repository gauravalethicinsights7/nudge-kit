"""specs/m7-orchestration.md: 'Exports: CSV + JSON for Veeva/Salesforce
suggestions; webhook stub.' Purely templated rendering of already-validated,
already-guardrail-passed Action[] — no LLM, no guardrail logic here (that ran
in models/guardrails.py before these Actions ever existed).
"""

from __future__ import annotations

import csv
import io
import json

from schemas.orchestration import Action

CSV_FIELDS = ["hcp_id", "channel", "content_ref", "suggested_date", "reason", "score", "action_status"]


def to_csv(actions: list[Action]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for action in actions:
        writer.writerow(
            {
                "hcp_id": str(action.hcp_id),
                "channel": action.channel,
                "content_ref": action.content_ref or "",
                "suggested_date": action.suggested_date.isoformat(),
                "reason": action.reason,
                "score": action.score,
                "action_status": action.action_status.value,
            }
        )
    return buffer.getvalue()


def to_json(actions: list[Action]) -> str:
    return json.dumps([json.loads(a.model_dump_json()) for a in actions], indent=2)


def webhook_stub(actions: list[Action], url: str | None = None) -> dict:
    """Stub per spec — no real endpoint exists yet. Returns the payload that
    would be POSTed, without making any network call, so callers/tests can
    inspect it directly."""
    return {"url": url, "count": len(actions), "payload": json.loads(to_json(actions))}

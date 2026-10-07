"""Shared test helper: a valid PersonaDraft-shaped JSON payload for a given
pack, so M3 agent tests don't each re-derive the full channel/signal list.
"""

from __future__ import annotations

import json

from schemas.enums import Driver
from schemas.pack import Pack

RUNG_TRANSITIONS = [
    ("unaware", "aware"),
    ("aware", "considering"),
    ("considering", "trialist"),
    ("trialist", "adopter"),
]


def valid_persona_draft_json(
    pack: Pack, name: str = "Test Persona", evidence_ids: list[str] | None = None, relative_weight: float = 1.0
) -> str:
    channel_id = pack.channels[0].id
    signal = pack.signals[0]

    draft = {
        "name": name,
        "beliefs": ["believes evidence matters"],
        "drivers_ranked": [d.value for d in Driver],
        "barriers_by_rung": {
            "aware": ["barrier a"],
            "considering": ["barrier b"],
            "trialist": ["barrier c"],
        },
        "evidence_needs": ["trial"],
        "channel_affinity": {c.id: 0.5 for c in pack.channels},
        "influence_network": ["peers"],
        "relative_weight": relative_weight,
        "evidence_ids": evidence_ids or [],
        "journey_steps": [
            {
                "from_rung": frm,
                "to_rung": to,
                "job": f"job {frm}->{to}",
                "barrier": "barrier",
                "proof": "proof",
                "lead_channels": [channel_id],
                "exit_signal": signal,
            }
            for frm, to in RUNG_TRANSITIONS
        ],
    }
    return json.dumps(draft)

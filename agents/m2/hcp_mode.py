"""The full per-HCP path of M2: assign_rung -> resolve potential -> tier /
opportunity / reachability -> group into Segments -> ranked TargetLists.
Purely deterministic (models/scores.py); no LLM calls in this module.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from models.scores import (
    assign_rung,
    assign_tier,
    build_reason,
    opportunity,
    percentile_rank,
    reachability,
)
from schemas.brand import Brand
from schemas.enums import Tier
from schemas.hcp import HCP, AdoptionState, Segment
from schemas.pack import Pack
from schemas.persona import Persona
from schemas.target_list import TargetList, TargetListEntry


def run_hcp_mode(
    brand: Brand,
    pack: Pack,
    hcps: list[HCP],
    target_share: float,
    personas_by_id: dict[UUID, Persona],
    as_of: date,
) -> tuple[list[AdoptionState], list[Segment], list[TargetList]]:
    adoption_states = [assign_rung(hcp, brand.id, pack, as_of) for hcp in hcps]
    rung_by_hcp_id = {s.hcp_id: s for s in adoption_states}

    potentials = [hcp.potential.value for hcp in hcps]

    scored = []
    for hcp in hcps:
        state = rung_by_hcp_id[hcp.id]
        persona = personas_by_id.get(hcp.persona_id) if hcp.persona_id else None
        potential = hcp.potential.value
        share = hcp.brand_share.value
        pctl = percentile_rank(potential, potentials)
        reach = reachability(hcp.access, pack, persona)
        opp = opportunity(potential, target_share, share, state.p_move_up, reach)
        tier = assign_tier(pctl, share, target_share, state.rung, reach, pack)
        reason = build_reason(potential, pctl, share, target_share, state.rung, state.p_move_up, reach, opp)
        scored.append(
            {
                "hcp": hcp,
                "tier": tier,
                "opportunity": opp,
                "reachability": reach,
                "reason": reason,
                "potential": potential,
                "share": share,
            }
        )

    segments: list[Segment] = []
    target_lists: list[TargetList] = []

    for tier in Tier:
        members = [s for s in scored if s["tier"] == tier]
        if not members:
            continue

        hcp_count = len(members)
        segment = Segment(
            brand_id=brand.id,
            name=f"{tier.value} segment",
            rule={"tier": tier.value},
            tier=tier,
            hcp_count=hcp_count,
            total_potential=sum(m["potential"] for m in members),
            avg_share=sum(m["share"] for m in members) / hcp_count,
            target_share=target_share,
            mode="hcp_level",
        )
        segments.append(segment)

        ranked = sorted(members, key=lambda m: m["opportunity"], reverse=True)
        entries = [
            TargetListEntry(
                hcp_id=m["hcp"].id,
                rank=i + 1,
                opportunity_score=m["opportunity"],
                reachability=m["reachability"],
                reason=m["reason"],
            )
            for i, m in enumerate(ranked)
        ]
        target_lists.append(TargetList(brand_id=brand.id, segment_id=segment.id, entries=entries))

    return adoption_states, segments, target_lists

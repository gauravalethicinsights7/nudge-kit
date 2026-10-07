from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from agents.m2.hcp_mode import run_hcp_mode
from agents.m2.segment_only import run_segment_only
from schemas.brand import Brand
from schemas.hcp import HCP, AdoptionState, Segment
from schemas.pack import Pack
from schemas.persona import Persona
from schemas.target_list import TargetList
from store.adoption_state_repo import AdoptionStateRepo
from store.segment_repo import SegmentRepo
from store.target_list_repo import TargetListRepo


@dataclass
class M2Result:
    adoption_states: list[AdoptionState]
    segments: list[Segment]
    target_lists: list[TargetList]
    mode: str


def run(
    brand: Brand,
    pack: Pack,
    hcps: list[HCP],
    target_share: float,
    session: Session,
    personas: list[Persona] | None = None,
    as_of: date | None = None,
) -> M2Result:
    """Empty `hcps` routes to segment-only mode, per specs/m2-segmentation.md."""
    as_of = as_of or date.today()

    if hcps:
        personas_by_id = {p.id: p for p in (personas or [])}
        adoption_states, segments, target_lists = run_hcp_mode(
            brand, pack, hcps, target_share, personas_by_id, as_of
        )
        mode = "hcp_level"
    else:
        adoption_states = []
        segments = run_segment_only(brand, pack, target_share)
        target_lists = []
        mode = "segment_only"

    saved_states = AdoptionStateRepo(session).add_many(adoption_states) if adoption_states else []
    saved_segments = SegmentRepo(session).add_many(segments) if segments else []
    saved_target_lists = TargetListRepo(session).add_many(target_lists) if target_lists else []

    return M2Result(
        adoption_states=saved_states,
        segments=saved_segments,
        target_lists=saved_target_lists,
        mode=mode,
    )

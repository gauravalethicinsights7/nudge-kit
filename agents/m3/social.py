"""social derivation path: thin wrapper over text_signal's shared pipeline,
same as call_notes but over social posts (specs/m3-personas.md: 'social: same
as call_notes on HCP posts'). hcp_ref is optional — a post's author can't
always be resolved to a specific HCP, and unresolvable posts simply don't
produce a PersonaAssignment.
"""

from __future__ import annotations

from pydantic import BaseModel

from agents.m3.finalize import DerivedPersona
from agents.m3.text_signal import TextSignalItem, run_text_signal_derivation
from schemas.brand import Brand
from schemas.enums import PersonaDerivation
from schemas.pack import Pack
from schemas.persona_assignment import PersonaAssignment
from store.evidence_repo import EvidenceRepo


class SocialPost(BaseModel):
    post_id: str
    hcp_ref: str | None = None
    text: str


def run_social(
    brand: Brand,
    pack: Pack,
    posts: list[SocialPost],
    evidence_repo: EvidenceRepo,
    *,
    run_record_repo=None,
) -> tuple[list[DerivedPersona], list[PersonaAssignment]]:
    items = [TextSignalItem(item_id=p.post_id, hcp_ref=p.hcp_ref, text=p.text) for p in posts]
    return run_text_signal_derivation(
        brand, pack, items, evidence_repo, PersonaDerivation.social, "social", run_record_repo=run_record_repo
    )

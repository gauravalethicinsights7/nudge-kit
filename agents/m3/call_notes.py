"""call_notes derivation path: thin wrapper over text_signal's shared
extract -> embed -> cluster -> finalize pipeline. Each note is tied to a
specific HCP (crm_id), so this path also produces PersonaAssignment rows.
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


class CallNote(BaseModel):
    note_id: str
    crm_id: str
    text: str


def run_call_notes(
    brand: Brand,
    pack: Pack,
    notes: list[CallNote],
    evidence_repo: EvidenceRepo,
    *,
    run_record_repo=None,
) -> tuple[list[DerivedPersona], list[PersonaAssignment]]:
    items = [TextSignalItem(item_id=n.note_id, hcp_ref=n.crm_id, text=n.text) for n in notes]
    return run_text_signal_derivation(
        brand,
        pack,
        items,
        evidence_repo,
        PersonaDerivation.call_notes,
        "call_notes",
        run_record_repo=run_record_repo,
    )

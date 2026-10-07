import json
import re

import pytest

from agents.m3.call_notes import CallNote, run_call_notes
from packs.loader import load_pack
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo
from tests.factories import make_brand
from tests.m3_support import valid_persona_draft_json

pytestmark = pytest.mark.integration


def test_run_call_notes_extracts_clusters_and_assigns_hcps(db_session, monkeypatch):
    pack = load_pack("india")
    brand = BrandRepo(db_session).add(make_brand())

    def fake_extract_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate({"claims": [f"claim about {variables['text'][:30]}"]})

    def fake_finalize_call(prompt_id, variables, output_model, **kwargs):
        cited_ids = re.findall(r"\[([0-9a-f-]{36})\]", variables["cluster_summary"])
        payload = json.loads(
            valid_persona_draft_json(
                pack,
                name=f"Persona for cluster of {variables['cluster_size']}",
                evidence_ids=cited_ids[:1],
                relative_weight=float(variables["cluster_size"]),
            )
        )
        return output_model.model_validate(payload, context=kwargs.get("validation_context"))

    monkeypatch.setattr("agents.m3.text_signal.call", fake_extract_call)
    monkeypatch.setattr("agents.m3.finalize.call", fake_finalize_call)

    notes = [
        CallNote(note_id="n1", crm_id="hcp1", text="Doctor worried about generic quality and evidence"),
        CallNote(note_id="n2", crm_id="hcp1", text="Doctor again raised bioequivalence data concerns"),
        CallNote(note_id="n3", crm_id="hcp2", text="Doctor focused on patient affordability and cost"),
        CallNote(note_id="n4", crm_id="hcp3", text="Doctor worried about GI tolerability and titration"),
        CallNote(note_id="n5", crm_id="hcp4", text="Doctor has very little consult time, wants convenience"),
        CallNote(note_id="n6", crm_id="hcp5", text="Doctor again cites cost as the main barrier"),
    ]

    derived, assignments = run_call_notes(brand, pack, notes, EvidenceRepo(db_session))

    assert len(derived) >= 1
    assert all(d.persona.assumption is False for d in derived)
    assert all(d.persona.evidence_ids for d in derived)
    assert all(d.persona.derivation.value == "call_notes" for d in derived)
    assert len(assignments) == 5  # 5 unique crm_ids across the 6 notes
    assert all(0.0 < a.confidence <= 1.0 for a in assignments)

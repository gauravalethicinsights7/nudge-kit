import json
import re

import pytest

from agents.m3.social import SocialPost, run_social
from packs.loader import load_pack
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo
from tests.factories import make_brand
from tests.m3_support import valid_persona_draft_json

pytestmark = pytest.mark.integration


def test_run_social_handles_posts_with_and_without_hcp_ref(db_session, monkeypatch):
    pack = load_pack("india")
    brand = BrandRepo(db_session).add(make_brand())

    def fake_extract_call(prompt_id, variables, output_model, **kwargs):
        return output_model.model_validate({"claims": [f"claim about {variables['text'][:30]}"]})

    def fake_finalize_call(prompt_id, variables, output_model, **kwargs):
        cited_ids = re.findall(r"\[([0-9a-f-]{36})\]", variables["cluster_summary"])
        payload = json.loads(
            valid_persona_draft_json(
                pack,
                name=f"Social persona {variables['cluster_size']}",
                evidence_ids=cited_ids[:1],
                relative_weight=float(variables["cluster_size"]),
            )
        )
        return output_model.model_validate(payload, context=kwargs.get("validation_context"))

    monkeypatch.setattr("agents.m3.text_signal.call", fake_extract_call)
    monkeypatch.setattr("agents.m3.finalize.call", fake_finalize_call)

    posts = [
        SocialPost(post_id="p1", hcp_ref="hcp1", text="Not convinced generics have the trial data"),
        SocialPost(post_id="p2", hcp_ref="hcp1", text="Still want to see bioequivalence evidence"),
        SocialPost(post_id="p3", hcp_ref=None, text="Anonymous post about cost pressure on patients"),
        SocialPost(post_id="p4", hcp_ref="hcp2", text="Cost is the main barrier for my patients"),
        SocialPost(post_id="p5", hcp_ref="hcp3", text="GI tolerability worries me with new starts"),
        SocialPost(post_id="p6", hcp_ref="hcp4", text="No time to review every new therapy in detail"),
    ]

    derived, assignments = run_social(brand, pack, posts, EvidenceRepo(db_session))

    assert len(derived) >= 1
    assert all(d.persona.derivation.value == "social" for d in derived)
    # only posts with an hcp_ref (5 of 6) contribute to PersonaAssignment
    assert len(assignments) == 4

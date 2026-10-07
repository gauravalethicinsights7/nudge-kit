import json
from uuid import uuid4

import pytest

from agents.m3.survey import SurveyResponse, run_survey
from packs.loader import load_pack
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo
from tests.factories import make_brand
from tests.m3_support import valid_persona_draft_json

pytestmark = pytest.mark.integration


def test_run_survey_clusters_numeric_items_and_derives_personas(db_session, monkeypatch):
    pack = load_pack("india")
    brand = BrandRepo(db_session).add(make_brand())

    def fake_finalize_call(prompt_id, variables, output_model, **kwargs):
        payload = json.loads(
            valid_persona_draft_json(
                pack,
                name=f"Survey persona {variables['cluster_size']}",
                evidence_ids=[str(uuid4())],
                relative_weight=float(variables["cluster_size"]),
            )
        )
        return output_model.model_validate(payload, context=kwargs.get("validation_context"))

    monkeypatch.setattr("agents.m3.finalize.call", fake_finalize_call)

    responses = [
        SurveyResponse(respondent_id=f"r{i}", items={"evidence_strength": 5.0, "cost": 1.0})
        for i in range(6)
    ] + [
        SurveyResponse(respondent_id=f"r{i + 6}", items={"evidence_strength": 1.0, "cost": 5.0})
        for i in range(6)
    ]

    derived = run_survey(brand, pack, responses, EvidenceRepo(db_session))

    assert len(derived) >= 1
    assert all(d.persona.derivation.value == "survey" for d in derived)
    assert all(d.persona.assumption is False for d in derived)
    assert all(d.persona.evidence_ids for d in derived)

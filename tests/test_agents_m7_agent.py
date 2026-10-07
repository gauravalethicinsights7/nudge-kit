from datetime import date
from uuid import uuid4

import pytest

from agents.m7.agent import run as run_m7
from exporters.nba import to_csv, to_json, webhook_stub
from ingest.content_library import load_content_library
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.enums import Access, Driver, Origin, Rung, Setting, Tier
from schemas.hcp import HCP, AdoptionState, Consent, ExternalIds, Geo
from schemas.persona import Persona
from store.brand_repo import BrandRepo
from tests.factories import make_brand, make_persona, make_segment

pytestmark = pytest.mark.integration


def _hcp(consent_email=True, consent_whatsapp=True) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id=str(uuid4())),
        name_hash="h",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=1000.0, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(email=consent_email, whatsapp=consent_whatsapp),
    )


def _persona_with_affinity(brand_id) -> Persona:
    persona = make_persona(brand_id)
    persona.channel_affinity = {
        "rep_visit": 0.9, "whatsapp": 0.6, "email": 0.5, "e_detailing": 0.4, "kol_peer": 0.3,
    }
    persona.drivers_ranked = [Driver.evidence_strength] + [d for d in Driver if d != Driver.evidence_strength]
    return persona


def test_m7_run_builds_journey_rules_and_guardrailed_actions(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")

    segments = [
        make_segment(brand.id),  # default tier=t1_grow
        make_segment(brand.id),
    ]
    segments[1].tier = Tier.t3_develop
    excluded_segment = make_segment(brand.id)
    excluded_segment.tier = Tier.t2_defend
    segments.append(excluded_segment)

    personas = [_persona_with_affinity(brand.id), _persona_with_affinity(brand.id)]

    hcps = [_hcp(), _hcp(consent_email=False, consent_whatsapp=False)]
    adoption_states = [
        AdoptionState(hcp_id=hcps[0].id, brand_id=brand.id, rung=Rung.aware, entered_on=date.today(), p_move_up=0.2),
        AdoptionState(hcp_id=hcps[1].id, brand_id=brand.id, rung=Rung.aware, entered_on=date.today(), p_move_up=0.2),
    ]

    content_library = load_content_library("fixtures/content_library_sample.yaml", brand.id)

    result = run_m7(brand, pack, db_session, segments, personas, hcps, adoption_states, content_library)

    # journey rules: exactly one per (T1/T3 segment) x persona
    t1_t3_segments = [s for s in segments if s.tier in {Tier.t1_grow, Tier.t3_develop}]
    assert len(result.journey_rules) == len(t1_t3_segments) * len(personas)
    for rule in result.journey_rules:
        assert rule.steps
        assert rule.steps[0].channel == "rep_visit"  # highest-affinity channel in _persona_with_affinity

    # a digital reinforcement step should follow rep_visit
    assert any(len(rule.steps) > 1 and rule.steps[1].wait_days == 2 for rule in result.journey_rules)

    # patient_support content is deliberately patient_directed=True -> never actioned
    assert all(a.channel != "patient_support" for a in result.actions)
    # chemist_trade has no approved content in the fixture -> never actioned
    assert all(a.channel != "chemist_trade" for a in result.actions)

    # the HCP with no consent never gets a whatsapp/email action
    no_consent_hcp_actions = [a for a in result.actions if a.hcp_id == hcps[1].id]
    assert all(a.channel not in {"whatsapp", "email"} for a in no_consent_hcp_actions)

    # top-k=3 respected per HCP
    from collections import Counter

    counts = Counter(a.hcp_id for a in result.actions)
    assert all(c <= 3 for c in counts.values())

    assert result.actions, "expected at least one guardrail-passing action"
    csv_text = to_csv(result.actions)
    assert "hcp_id" in csv_text.splitlines()[0]
    assert len(csv_text.splitlines()) == len(result.actions) + 1

    json_text = to_json(result.actions)
    assert len(json_text) > 0

    stub = webhook_stub(result.actions, url=None)
    assert stub["count"] == len(result.actions)


def test_m7_run_emits_content_brief_when_no_usable_content_exists_for_top_channel(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    pack = load_pack("india")

    segment = make_segment(brand.id)  # tier=t1_grow
    persona = _persona_with_affinity(brand.id)
    persona.channel_affinity = {"chemist_trade": 0.9}  # a channel the fixture library has no approved content for

    result = run_m7(brand, pack, db_session, [segment], [persona], [], [], content_library=[])

    assert len(result.journey_rules) == 1
    rule = result.journey_rules[0]
    assert rule.steps[0].channel == "chemist_trade"
    assert rule.steps[0].content_ref is None
    assert len(result.content_briefs) == 1
    assert result.content_briefs[0].channel == "chemist_trade"
    assert result.content_briefs[0].persona_id == persona.id

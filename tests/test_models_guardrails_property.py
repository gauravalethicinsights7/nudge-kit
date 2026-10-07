"""specs/m7-orchestration.md Done-when: 'NBA never suggests a channel without
consent (property test)'. No `hypothesis` dependency in this project — a
manual randomized sweep with a fixed seed over the real pack's channels,
matching this repo's existing test style (see tests/test_models_optimiser.py).
"""

import random
from datetime import date

from models.guardrails import NO_CONSENT, check_action_guardrails
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.content import ContentModule
from schemas.enums import Access, Driver, MlrStatus, Origin, Setting
from schemas.hcp import HCP, Consent, ExternalIds, Geo

PACK = load_pack("india")
CONSENT_REQUIRING_CHANNELS = [pc.id for pc in PACK.channels if pc.requires_consent]


def _random_hcp(rng: random.Random) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="c"),
        name_hash="h",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=rng.uniform(1, 5000), source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(email=False, whatsapp=False, sms=False),  # deliberately no consent, any channel
    )


def _random_content(rng: random.Random) -> ContentModule:
    return ContentModule(
        brand_id=__import__("uuid").uuid4(),
        name="c",
        driver=rng.choice(list(Driver)),
        claim="claim",
        format="email",
        mlr_status=rng.choice(list(MlrStatus)),
        on_label=rng.choice([True, False]),
        is_comparative=rng.choice([True, False]),
        comparative_approved=rng.choice([True, False]),
        patient_directed=rng.choice([True, False]),
        exceeds_pack_limit=rng.choice([True, False]),
    )


def test_no_consent_channels_are_never_allowed_regardless_of_other_flags():
    assert CONSENT_REQUIRING_CHANNELS, "pack must define at least one consent-requiring channel for this test to mean anything"
    rng = random.Random(1234)
    for _ in range(500):
        hcp = _random_hcp(rng)
        content = _random_content(rng)
        channel_ref = rng.choice(CONSENT_REQUIRING_CHANNELS)
        recent_touch_count = rng.randint(0, 10)
        unanswered_touch_count = rng.randint(0, 10)

        violations = check_action_guardrails(
            hcp, channel_ref, content, PACK,
            recent_touch_count=recent_touch_count, unanswered_touch_count=unanswered_touch_count,
        )
        assert NO_CONSENT in violations, (
            f"channel={channel_ref} content={content} touches=({recent_touch_count},{unanswered_touch_count})"
        )

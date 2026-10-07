from datetime import date

from agents.m2.hcp_mode import run_hcp_mode
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.enums import Access, Origin
from schemas.hcp import HCP, Consent, ExternalIds, Geo
from tests.factories import make_brand

AS_OF = date(2026, 9, 30)


def _hcp(specialty, setting, city_tier, volume, share, access) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id=f"c-{specialty}-{volume}"),
        name_hash="h",
        specialty=specialty,
        setting=setting,
        geo=Geo(city_tier=city_tier),
        potential=ProvNumber(value=0.0, source="x", origin=Origin.estimated, as_of=AS_OF, confidence=0.0),
        brand_share=ProvNumber(value=share, source="x", origin=Origin.estimated, as_of=AS_OF, confidence=0.5),
        access=access,
        consent=Consent(),
        patient_volume_estimate=volume,
    )


def test_run_hcp_mode_builds_segments_and_ranked_target_lists():
    pack = load_pack("india")
    brand = make_brand()

    hcps = [
        _hcp("endocrinologist", "hospital", "metro", 200.0, 0.01, Access.open),
        _hcp("diabetologist", "clinic", "metro", 150.0, 0.02, Access.open),
        _hcp("gp", "clinic", "tier3", 5.0, 0.0, Access.no_see),
    ]
    for hcp in hcps:
        hcp.potential.value = hcp.patient_volume_estimate  # simplify: pre-resolve

    adoption_states, segments, target_lists = run_hcp_mode(
        brand, pack, hcps, target_share=0.10, personas_by_id={}, as_of=AS_OF
    )

    assert len(adoption_states) == 3
    assert all(s.rung.value == "aware" for s in adoption_states)  # no rung_rules in either pack

    assert segments, "expected at least one segment"
    assert sum(s.hcp_count for s in segments) == 3

    all_entries = [e for tl in target_lists for e in tl.entries]
    assert len(all_entries) == 3
    assert all(e.reason.strip() for e in all_entries)

    # each target list is individually ranked by opportunity, descending
    for tl in target_lists:
        scores = [e.opportunity_score for e in tl.entries]
        assert scores == sorted(scores, reverse=True)
        assert [e.rank for e in tl.entries] == list(range(1, len(tl.entries) + 1))

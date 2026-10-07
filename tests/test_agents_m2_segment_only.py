from agents.m2.segment_only import run_segment_only
from packs.loader import load_pack
from tests.factories import make_brand


def test_segment_only_mode_produces_flagged_zero_headcount_segments():
    pack = load_pack("india")
    brand = make_brand()

    segments = run_segment_only(brand, pack, target_share=0.05)

    assert segments, "expected candidate segments from pack categories"
    assert all(s.mode == "segment_only" for s in segments)
    assert all(s.hcp_count == 0 for s in segments)
    assert all(s.total_potential > 0 for s in segments)
    # specialty x setting x city_tier cartesian product from the india pack
    expected_count = (
        len(pack.potential_proxies.specialty_weight)
        * len(pack.potential_proxies.setting_weight)
        * len(pack.potential_proxies.city_tier_weight)
    )
    assert len(segments) == expected_count

import pytest

from agents.m6.channels import build_channels_from_pack
from packs.loader import load_pack


@pytest.mark.parametrize("market", ["india", "us"])
def test_build_channels_from_pack_produces_valid_channels(market):
    pack = load_pack(market)
    channels = build_channels_from_pack(pack)
    assert len(channels) == len(pack.channels)
    refs = {c.channel_ref for c in channels}
    assert refs == {pc.id for pc in pack.channels}
    for c in channels:
        assert c.unit_cost is not None
        assert c.curve.beta is not None  # placeholder fills null beta
        assert 0.0 <= c.curve.alpha


def test_build_channels_from_pack_flags_placeholder_unit_cost():
    pack = load_pack("india")
    channels = build_channels_from_pack(pack)
    # both shipped packs have unit_cost=null for every channel today
    for c in channels:
        assert c.unit_cost.origin.value == "estimated"
        assert c.unit_cost.confidence < 0.5


def test_build_channels_from_pack_sets_rep_visit_capacity_from_rep_count():
    pack = load_pack("india")
    channels = build_channels_from_pack(pack, rep_count=100)
    rep_visit = next(c for c in channels if c.channel_ref == "rep_visit")
    assert rep_visit.capacity == 100 * 22 * 10


def test_build_channels_from_pack_leaves_capacity_none_without_rep_count():
    pack = load_pack("india")
    channels = build_channels_from_pack(pack)
    rep_visit = next(c for c in channels if c.channel_ref == "rep_visit")
    assert rep_visit.capacity is None

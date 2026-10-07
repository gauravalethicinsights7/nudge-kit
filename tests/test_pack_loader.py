import pytest
from pydantic import ValidationError

from packs.loader import load_pack
from schemas.pack import Pack


def test_load_pack_india():
    pack = load_pack("india")
    assert pack.market.value == "india"
    assert pack.currency == "INR"
    assert any(c.id == "rep_visit" for c in pack.channels)


def test_load_pack_us():
    pack = load_pack("us")
    assert pack.market.value == "us"
    assert pack.currency == "USD"


def test_pack_rejects_unknown_top_level_key():
    pack = load_pack("india")
    raw = pack.model_dump(mode="json")
    raw["unknown_field_that_should_not_exist"] = True
    with pytest.raises(ValidationError):
        Pack.model_validate(raw)

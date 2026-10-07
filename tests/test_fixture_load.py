import pytest

from ingest.fixture_loader import load_fixture

pytestmark = pytest.mark.integration


def test_fixture_loads_brand_and_seed_evidence(db_session):
    brand, evidence = load_fixture(db_session, "brand_s_semaglutide_india")

    assert brand.name == "Brand S"
    assert brand.molecule == "semaglutide"
    assert len(evidence) == 5
    assert all(e.brand_id == brand.id for e in evidence)
    assert all(e.source_url for e in evidence)

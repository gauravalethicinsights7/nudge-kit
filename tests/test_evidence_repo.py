import uuid
from datetime import date

import pytest

from schemas.enums import EvidenceType, Origin
from schemas.evidence import Evidence
from store.brand_repo import BrandRepo
from store.evidence_repo import EvidenceRepo
from tests.factories import make_brand

pytestmark = pytest.mark.integration


def _evidence(brand_id, claim, url="https://example.com/a"):
    return Evidence(
        brand_id=brand_id,
        source="test",
        origin=Origin.external,
        as_of=date.today(),
        confidence=0.7,
        type=EvidenceType.market,
        claim=claim,
        source_url=url,
    )


def test_add_search_get_many_round_trip(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    repo = EvidenceRepo(db_session)
    claim = f"Unique test claim {uuid.uuid4()}"

    added = repo.add(_evidence(brand.id, claim))
    assert added.id is not None
    assert added.embedding is not None
    assert len(added.embedding) == 384

    fetched = repo.get_many([added.id])
    assert len(fetched) == 1
    assert fetched[0].claim == claim

    results = repo.search(claim, brand_id=brand.id, k=5)
    assert any(r.id == added.id for r in results)

    results_wrong_type = repo.search(claim, brand_id=brand.id, types=[EvidenceType.regulatory], k=5)
    assert all(r.id != added.id for r in results_wrong_type)


def test_add_deduplicates_on_url_and_claim(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    repo = EvidenceRepo(db_session)
    claim = f"Dedup test claim {uuid.uuid4()}"
    url = "https://example.com/dup"

    first = repo.add(_evidence(brand.id, claim, url))
    second = repo.add(_evidence(brand.id, claim, url))

    assert first.id == second.id

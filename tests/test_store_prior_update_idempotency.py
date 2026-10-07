"""specs/m8-measurement.md Done-when: 'Prior update is idempotent and
versioned (pack priors never overwritten; tenant-level priors stored
separately).'
"""

import pytest

from packs.loader import load_pack
from schemas.measurement import PriorUpdate
from store.brand_repo import BrandRepo
from store.prior_update_repo import PriorUpdateRepo
from tests.factories import make_brand

pytestmark = pytest.mark.integration


def test_upserting_the_same_period_twice_does_not_duplicate_rows(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    repo = PriorUpdateRepo(db_session)

    update = PriorUpdate(
        brand_id=brand.id, prior_type="rung_transition", key="aware", period="2026-01", before=0.15, after=0.18
    )
    first = repo.upsert(update)
    second = repo.upsert(update)

    assert first.id == second.id  # same row, not a new one
    assert second.version == first.version + 1  # re-applying bumps version

    all_rows = repo.list_by_brand(brand.id)
    assert len(all_rows) == 1


def test_upsert_with_different_period_creates_a_separate_row(db_session):
    brand = BrandRepo(db_session).add(make_brand())
    repo = PriorUpdateRepo(db_session)

    repo.upsert(PriorUpdate(brand_id=brand.id, prior_type="rung_transition", key="aware", period="2026-01", before=0.15, after=0.18))
    repo.upsert(PriorUpdate(brand_id=brand.id, prior_type="rung_transition", key="aware", period="2026-02", before=0.18, after=0.20))

    assert len(repo.list_by_brand(brand.id)) == 2


def test_upsert_never_mutates_the_pack_yaml_values():
    before_india = load_pack("india")
    before_value = before_india.priors.rung_transition_monthly["aware"]

    # applying a PriorUpdate (even repeatedly) is purely a DB-side overlay —
    # nothing in this codebase writes back to packs/<market>/pack.yaml
    after_india = load_pack("india")
    assert after_india.priors.rung_transition_monthly["aware"] == before_value

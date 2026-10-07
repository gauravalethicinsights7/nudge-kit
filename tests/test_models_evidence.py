from datetime import date

import pytest

from models.evidence import confidence_score
from schemas.enums import SourceCategory

AS_OF = date(2026, 9, 30)
RECENT = date(2026, 1, 1)
OLD = date(2020, 1, 1)  # > 3 years before AS_OF


@pytest.mark.parametrize(
    "category,expected",
    [
        (SourceCategory.peer_reviewed_guideline_regulator, 0.9),
        (SourceCategory.audit_market_vendor, 0.8),
        (SourceCategory.reputable_press, 0.6),
        (SourceCategory.vendor_blog, 0.4),
        (SourceCategory.forum, 0.3),
        (SourceCategory.other, 0.5),
    ],
)
def test_base_score_recent_date(category, expected):
    assert confidence_score(category, RECENT, AS_OF) == pytest.approx(expected)


@pytest.mark.parametrize(
    "category,expected",
    [
        (SourceCategory.peer_reviewed_guideline_regulator, 0.7),
        (SourceCategory.audit_market_vendor, 0.6),
        (SourceCategory.reputable_press, 0.4),
        (SourceCategory.vendor_blog, 0.2),
        (SourceCategory.forum, 0.1),
    ],
)
def test_age_penalty_applied_past_three_years(category, expected):
    assert confidence_score(category, OLD, AS_OF) == pytest.approx(expected)


def test_no_penalty_when_published_date_unknown():
    assert confidence_score(SourceCategory.forum, None, AS_OF) == pytest.approx(0.3)


def test_score_clamped_to_zero_floor():
    # a category near the age-penalty floor should never go negative
    assert confidence_score(SourceCategory.forum, OLD, AS_OF) >= 0.0


def test_score_never_exceeds_one():
    for category in SourceCategory:
        assert confidence_score(category, RECENT, AS_OF) <= 1.0

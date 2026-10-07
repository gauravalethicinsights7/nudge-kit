from uuid import uuid4

from ingest.engagement_events_csv import load_engagement_events_csv
from schemas.engagement import EngagementEvent

FIXTURE_PATH = "fixtures/engagement_events_sample.csv"


def test_load_engagement_events_csv_round_trips():
    brand_id = uuid4()
    events = load_engagement_events_csv(FIXTURE_PATH, brand_id)
    assert len(events) == 8
    assert all(isinstance(e, EngagementEvent) for e in events)
    assert all(e.brand_id == brand_id for e in events)


def test_load_engagement_events_csv_parses_dates_and_channels():
    events = load_engagement_events_csv(FIXTURE_PATH, uuid4())
    first = events[0]
    assert first.channel == "rep_visit"
    assert first.depth == "attended"
    assert first.occurred_at.isoformat() == "2026-01-05"
    assert first.period == "2026-01"

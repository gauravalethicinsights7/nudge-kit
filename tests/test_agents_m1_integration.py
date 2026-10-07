import os

import pytest

from evals.run import run_m1

pytestmark = pytest.mark.live


@pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SERPER_API_KEY")),
    reason="requires ANTHROPIC_API_KEY and SERPER_API_KEY",
)
def test_m1_live_fixture_run_meets_done_when_bar():
    report = run_m1("brand_s_semaglutide_india")

    checks_by_name = {c["name"]: c for c in report["checks"]}
    assert checks_by_name["evidence_count_at_least_25"]["pass"], report
    assert checks_by_name["known_facts_matched"]["pass"], report["unmatched_known_facts"]

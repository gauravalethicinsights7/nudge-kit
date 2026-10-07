import os

import pytest

from evals.run import run_m3

pytestmark = pytest.mark.live


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="requires ANTHROPIC_API_KEY")
def test_m3_live_fixture_run_meets_done_when_bar():
    report = run_m3("brand_s_semaglutide_india")

    checks_by_name = {c["name"]: c for c in report["checks"]}
    assert checks_by_name["synthetic_shares_sum_to_one"]["pass"], report
    assert checks_by_name["synthetic_distinctness"]["pass"], report
    assert checks_by_name["call_notes_shares_sum_to_one"]["pass"], report

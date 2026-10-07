import os

import pytest

from evals.run import run_m4

pytestmark = pytest.mark.live


@pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SERPER_API_KEY")),
    reason="requires ANTHROPIC_API_KEY and SERPER_API_KEY",
)
def test_m4_live_fixture_run_meets_done_when_bar():
    report = run_m4("brand_s_semaglutide_india")

    checks_by_name = {c["name"]: c for c in report["checks"]}
    assert checks_by_name["grid_is_dense"]["pass"], report
    assert checks_by_name["esov_skipped_with_note"]["pass"], report

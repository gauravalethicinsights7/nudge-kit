import os

import pytest

from evals.run import run_m5

pytestmark = pytest.mark.live


@pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("SERPER_API_KEY")),
    reason="requires ANTHROPIC_API_KEY and SERPER_API_KEY (full M1->M5 chain)",
)
def test_m5_live_full_chain_meets_done_when_bar():
    report = run_m5("brand_s_semaglutide_india")

    checks_by_name = {c["name"]: c for c in report["checks"]}
    assert checks_by_name["forecast_has_three_sensitivity_assumptions"]["pass"], report
    assert checks_by_name["no_block_severity_compliance_flags"]["pass"], report
    assert checks_by_name["every_objective_has_baseline_target_due"]["pass"], report

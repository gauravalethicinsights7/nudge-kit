import json
import sys

from evals.harness import DeterministicCheck, build_report, run_deterministic_checks
from evals.run import REPORTS_DIR, main, run


def test_build_report_shape_deterministic_only():
    checks = run_deterministic_checks(
        [DeterministicCheck("always_true", lambda: (True, "ok")), DeterministicCheck("always_false", lambda: (False, "nope"))]
    )
    report = build_report(checks, rubric=[])
    assert report["checks"] == [
        {"name": "always_true", "pass": True, "detail": "ok"},
        {"name": "always_false", "pass": False, "detail": "nope"},
    ]
    assert report["rubric"] == []
    assert report["overall"]["pass"] is False  # one check failed


def test_dummy_module_runs_against_fixture():
    report = run("dummy", "brand_s_semaglutide_india")
    assert report["overall"]["pass"] is True
    names = {c["name"] for c in report["checks"]}
    assert names == {"fixture_exists", "fixture_has_brand", "pack_loads_for_fixture_market"}


def test_cli_writes_report_file(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run.py", "--module", "dummy", "--fixture", "brand_s_semaglutide_india"])
    main()
    out_path = REPORTS_DIR / "dummy_brand_s_semaglutide_india.json"
    assert out_path.exists()
    report = json.loads(out_path.read_text())
    assert report["overall"]["pass"] is True

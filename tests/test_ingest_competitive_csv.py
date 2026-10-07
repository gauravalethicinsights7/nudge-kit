from pathlib import Path

from ingest.competitive_csv import load_promo_audit_csv, load_share_audit_csv


def test_load_share_audit_csv(tmp_path: Path):
    path = tmp_path / "share.csv"
    path.write_text("# comment\nbrand,period,share\nBrandA,2026-01,20.0\nBrandB,2026-01,10.0\n")

    result = load_share_audit_csv(path)

    assert result == {("BrandA", "2026-01"): 20.0, ("BrandB", "2026-01"): 10.0}


def test_load_promo_audit_csv_computes_sov_from_activity(tmp_path: Path):
    path = tmp_path / "promo.csv"
    path.write_text(
        "# comment\n"
        "brand,channel,period,activity\n"
        "BrandA,rep_visit,2026-01,300\n"
        "BrandA,email,2026-01,100\n"
        "BrandB,rep_visit,2026-01,600\n"
    )

    result = load_promo_audit_csv(path)

    # BrandA: 400 of 1000 total = 40%; BrandB: 600 of 1000 = 60%
    assert result[("BrandA", "2026-01")] == 40.0
    assert result[("BrandB", "2026-01")] == 60.0

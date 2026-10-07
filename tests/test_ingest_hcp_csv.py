from pathlib import Path

from ingest.hcp_csv import load_hcp_csv
from packs.loader import load_pack


def test_load_hcp_csv_skips_comment_header_and_resolves_potential(tmp_path: Path):
    csv_path = tmp_path / "hcps.csv"
    csv_path.write_text(
        "# a comment line that must be skipped\n"
        "# another comment line\n"
        "crm_id,specialty,setting,state,city,city_tier,territory_id,rep_class,access,"
        "consent_email,consent_whatsapp,patient_volume_estimate\n"
        "HCP00001,diabetologist,clinic,Maharashtra,Mumbai,metro,MA-1,A,open,True,True,50.0\n"
        "HCP00002,gp,hospital,Delhi,New Delhi,metro,DL-2,C,restricted,False,True,\n"
    )

    pack = load_pack("india")
    hcps = load_hcp_csv(csv_path, pack)

    assert len(hcps) == 2

    first = hcps[0]
    assert first.external_ids.crm_id == "HCP00001"
    assert first.specialty == "diabetologist"
    assert first.patient_volume_estimate == 50.0
    assert first.rep_class == "A"
    assert first.potential.origin.value == "estimated"
    assert first.potential.value > 0

    second = hcps[1]
    assert second.patient_volume_estimate is None
    assert second.potential.confidence < 0.5  # no volume signal available

"""specs/m7-orchestration.md Done-when: 'Guardrail red-team suite
(evals/gold/m7_redteam.yaml, >= 30 cases) -> 0 violations exported.'
"""

from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from models.guardrails import check_action_guardrails
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.content import ContentModule
from schemas.enums import Access, Driver, Origin, Setting
from schemas.hcp import HCP, Consent, ExternalIds, Geo

GOLD_PATH = Path(__file__).parent.parent / "evals" / "gold" / "m7_redteam.yaml"
PACK = load_pack("india")


def _load_cases() -> list[dict]:
    return yaml.safe_load(GOLD_PATH.read_text())["cases"]


def _hcp_for(case: dict) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="c"),
        name_hash="h",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=1000.0, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(**case.get("consent", {})),
    )


def _content_for(case: dict) -> ContentModule:
    return ContentModule(
        brand_id=uuid4(),
        name=case["id"],
        driver=Driver.efficacy,
        claim="claim",
        format="email",
        **case["content"],
    )


CASES = _load_cases()


def test_gold_file_has_at_least_30_cases():
    assert len(CASES) >= 30


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_redteam_case_matches_expected_violations(case):
    hcp = _hcp_for(case)
    content = _content_for(case)
    violations = check_action_guardrails(
        hcp,
        case["channel"],
        content,
        PACK,
        recent_touch_count=case.get("recent_touch_count", 0),
        unanswered_touch_count=case.get("unanswered_touch_count", 0),
    )
    assert bool(violations) == case["expect_blocked"], f"{case['id']}: {case['description']} -> got {violations}"
    assert set(violations) == set(case["expect_reasons"]), f"{case['id']}: {case['description']} -> got {violations}"


def test_zero_violations_survive_a_simulated_export():
    """The literal Done-when bar: filter every case through the guardrail,
    and confirm exactly the cases marked expect_blocked=false survive — i.e.
    0 of the 'should be blocked' cases ever reach a simulated export."""
    exported_ids = set()
    for case in CASES:
        hcp = _hcp_for(case)
        content = _content_for(case)
        violations = check_action_guardrails(
            hcp,
            case["channel"],
            content,
            PACK,
            recent_touch_count=case.get("recent_touch_count", 0),
            unanswered_touch_count=case.get("unanswered_touch_count", 0),
        )
        if not violations:
            exported_ids.add(case["id"])

    expected_allowed_ids = {c["id"] for c in CASES if not c["expect_blocked"]}
    blocked_ids_that_leaked = exported_ids - expected_allowed_ids
    assert not blocked_ids_that_leaked, f"guardrail-violating cases leaked into export: {blocked_ids_that_leaked}"
    assert exported_ids == expected_allowed_ids

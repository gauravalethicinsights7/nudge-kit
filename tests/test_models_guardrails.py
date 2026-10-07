from datetime import date

from models.guardrails import (
    EXCEEDS_PACK_COMPLIANCE_LIMIT,
    FREQUENCY_CAP_EXCEEDED,
    MLR_NOT_APPROVED,
    NO_CONSENT,
    OFF_LABEL,
    PATIENT_DIRECTED_RX_PROMOTION,
    SUPPRESSED_CHANNEL,
    UNAPPROVED_COMPARATIVE_CLAIM,
    check_action_guardrails,
    content_is_usable,
)
from packs.loader import load_pack
from schemas.base import ProvNumber
from schemas.content import ContentModule
from schemas.enums import Access, Driver, MlrStatus, Origin, Setting
from schemas.hcp import HCP, Consent, ExternalIds, Geo

PACK = load_pack("india")


def _hcp(**consent_kwargs) -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="c1"),
        name_hash="h1",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(),
        potential=ProvNumber(value=1000.0, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        brand_share=ProvNumber(value=0.1, source="t", origin=Origin.estimated, as_of=date.today(), confidence=0.5),
        access=Access.open,
        consent=Consent(**consent_kwargs),
    )


def _content(**overrides) -> ContentModule:
    defaults = dict(
        brand_id=__import__("uuid").uuid4(),
        name="c",
        driver=Driver.efficacy,
        claim="claim",
        format="email",
        mlr_status=MlrStatus.approved,
    )
    defaults.update(overrides)
    return ContentModule(**defaults)


def test_clean_action_has_no_violations():
    hcp = _hcp(email=True)
    assert check_action_guardrails(hcp, "email", _content(), PACK) == []


def test_no_consent_blocked():
    hcp = _hcp(email=False)
    violations = check_action_guardrails(hcp, "email", _content(), PACK)
    assert NO_CONSENT in violations


def test_consent_not_required_for_rep_visit():
    hcp = _hcp()  # no consent flags set at all
    assert check_action_guardrails(hcp, "rep_visit", _content(), PACK) == []


def test_mlr_not_approved_blocked():
    hcp = _hcp(email=True)
    violations = check_action_guardrails(hcp, "email", _content(mlr_status=MlrStatus.submitted), PACK)
    assert MLR_NOT_APPROVED in violations


def test_off_label_blocked():
    hcp = _hcp(email=True)
    violations = check_action_guardrails(hcp, "email", _content(on_label=False), PACK)
    assert OFF_LABEL in violations


def test_unapproved_comparative_claim_blocked():
    hcp = _hcp(email=True)
    violations = check_action_guardrails(
        hcp, "email", _content(is_comparative=True, comparative_approved=False), PACK
    )
    assert UNAPPROVED_COMPARATIVE_CLAIM in violations


def test_approved_comparative_claim_not_blocked_on_that_dimension():
    hcp = _hcp(email=True)
    violations = check_action_guardrails(
        hcp, "email", _content(is_comparative=True, comparative_approved=True), PACK
    )
    assert UNAPPROVED_COMPARATIVE_CLAIM not in violations


def test_unrecognized_pack_consent_field_fails_closed():
    """india's patient_support channel declares consent_field:
    patient_programme, which isn't a field on the fixed Consent schema
    (email/whatsapp/sms). This must fail closed (blocked), never silently
    grant access — see models/guardrails.py::_has_consent's comment."""
    hcp = _hcp(email=True, whatsapp=True, sms=True)  # every real consent flag set
    violations = check_action_guardrails(hcp, "patient_support", _content(), PACK)
    assert NO_CONSENT in violations


def test_patient_directed_content_blocked():
    hcp = _hcp()
    violations = check_action_guardrails(hcp, "patient_support", _content(patient_directed=True), PACK)
    assert PATIENT_DIRECTED_RX_PROMOTION in violations


def test_exceeds_pack_limit_blocked():
    hcp = _hcp()
    violations = check_action_guardrails(hcp, "rep_visit", _content(exceeds_pack_limit=True), PACK)
    assert EXCEEDS_PACK_COMPLIANCE_LIMIT in violations


def test_frequency_cap_exceeded_blocked():
    hcp = _hcp(whatsapp=True)
    cap = PACK.frequency_caps["whatsapp"]
    violations = check_action_guardrails(hcp, "whatsapp", _content(), PACK, recent_touch_count=cap)
    assert FREQUENCY_CAP_EXCEEDED in violations


def test_under_frequency_cap_not_blocked_on_that_dimension():
    hcp = _hcp(whatsapp=True)
    cap = PACK.frequency_caps["whatsapp"]
    violations = check_action_guardrails(hcp, "whatsapp", _content(), PACK, recent_touch_count=cap - 1)
    assert FREQUENCY_CAP_EXCEEDED not in violations


def test_suppressed_after_n_unanswered_touches():
    hcp = _hcp(email=True)
    violations = check_action_guardrails(
        hcp, "email", _content(), PACK, unanswered_touch_count=PACK.suppress_after
    )
    assert SUPPRESSED_CHANNEL in violations


def test_content_is_usable_true_for_clean_content():
    assert content_is_usable(_content()) is True


def test_content_is_usable_false_when_not_on_label():
    assert content_is_usable(_content(on_label=False)) is False


def test_multiple_violations_all_reported():
    hcp = _hcp(email=False)
    violations = check_action_guardrails(hcp, "email", _content(mlr_status=MlrStatus.none, on_label=False), PACK)
    assert NO_CONSENT in violations
    assert MLR_NOT_APPROVED in violations
    assert OFF_LABEL in violations

"""M7's compliance guardrail (specs/m7-orchestration.md's "Guardrails (must
pass before export)" section; CLAUDE.md rule 6: "compliance guardrails run
before any output leaves M5/M7"). Every check here is a pure, structural
function — no text-phrase heuristics like M5's models/plan.py::check_compliance,
because every guardrail M7 lists is mechanically checkable from typed fields
(consent, mlr_status, on_label, ...) rather than free-text prose.

Two real data gaps this module can't fabricate its way around (see the
approved M7 plan):
- Per-HCP touch history (frequency cap / suppress-after tracking) isn't
  persisted anywhere yet, so `recent_touch_count`/`unanswered_touch_count`
  are explicit caller-supplied parameters, not looked up from a real store.
- UCPMP-style numeric caps (gift value, sample count) can't be computed from
  anything in this build — `ContentModule.exceeds_pack_limit` is a
  pre-computed flag a real gift/sample-tracking system would set; this
  module simply respects it.
"""

from __future__ import annotations

from schemas.content import ContentModule
from schemas.enums import MlrStatus
from schemas.hcp import HCP
from schemas.pack import Pack

NO_CONSENT = "no_consent"
MLR_NOT_APPROVED = "mlr_not_approved"
OFF_LABEL = "off_label"
UNAPPROVED_COMPARATIVE_CLAIM = "unapproved_comparative_claim"
PATIENT_DIRECTED_RX_PROMOTION = "patient_directed_rx_promotion"
EXCEEDS_PACK_COMPLIANCE_LIMIT = "exceeds_pack_compliance_limit"
FREQUENCY_CAP_EXCEEDED = "frequency_cap_exceeded"
SUPPRESSED_CHANNEL = "suppressed_channel"


def _has_consent(hcp: HCP, pack: Pack, channel_ref: str) -> bool:
    pack_channel = next((pc for pc in pack.channels if pc.id == channel_ref), None)
    if pack_channel is None or not pack_channel.requires_consent:
        return True
    if not pack_channel.consent_field:
        return True
    # Fails closed, deliberately, when a pack names a consent_field the fixed
    # Consent schema (email/whatsapp/sms, per specs/00-foundations.md) doesn't
    # have — e.g. india's patient_support channel declares consent_field:
    # patient_programme, which isn't a Consent field. Rather than silently
    # granting access on an unrecognized field, this treats it as "no
    # consent on record" (getattr's default), which is the safe guardrail
    # direction; the pack's own consent_field name is a real data
    # inconsistency worth fixing in packs/india/pack.yaml, out of scope here.
    return bool(getattr(hcp.consent, pack_channel.consent_field, False))


def content_violations(content: ContentModule) -> list[str]:
    """The content-level subset of check_action_guardrails' checks (mlr,
    on-label, comparative sign-off, patient-directed, pack-limit) — usable on
    their own wherever an HCP/consent context doesn't exist yet, e.g.
    resolving a JourneyRule step's content_ref at the segment x persona
    template level (see agents/m7/agent.py)."""
    violations: list[str] = []
    if content.mlr_status != MlrStatus.approved:
        violations.append(MLR_NOT_APPROVED)
    if not content.on_label:
        violations.append(OFF_LABEL)
    if content.is_comparative and not content.comparative_approved:
        violations.append(UNAPPROVED_COMPARATIVE_CLAIM)
    if content.patient_directed:
        violations.append(PATIENT_DIRECTED_RX_PROMOTION)
    if content.exceeds_pack_limit:
        violations.append(EXCEEDS_PACK_COMPLIANCE_LIMIT)
    return violations


def content_is_usable(content: ContentModule) -> bool:
    return not content_violations(content)


def check_action_guardrails(
    hcp: HCP,
    channel_ref: str,
    content: ContentModule,
    pack: Pack,
    recent_touch_count: int = 0,
    unanswered_touch_count: int = 0,
) -> list[str]:
    """Returns violation reason codes for suggesting `content` on `channel_ref`
    to `hcp`; empty list means the action is allowed. Every spec guardrail
    bullet maps to exactly one check here (see module docstring)."""
    violations: list[str] = content_violations(content)

    if not _has_consent(hcp, pack, channel_ref):
        violations.append(NO_CONSENT)

    freq_cap = pack.frequency_caps.get(channel_ref)
    if freq_cap is not None and recent_touch_count >= freq_cap:
        violations.append(FREQUENCY_CAP_EXCEEDED)
    if unanswered_touch_count >= pack.suppress_after:
        violations.append(SUPPRESSED_CHANNEL)

    return violations

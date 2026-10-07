from enum import Enum


class Status(str, Enum):
    draft = "draft"
    approved = "approved"
    superseded = "superseded"


class Origin(str, Enum):
    external = "external"
    internal = "internal"
    estimated = "estimated"


class Market(str, Enum):
    india = "india"
    us = "us"


class LifecycleStage(str, Enum):
    pre_launch = "pre_launch"
    launch = "launch"
    growth = "growth"
    mature = "mature"
    loe = "loe"


class Rung(str, Enum):
    unaware = "unaware"
    aware = "aware"
    considering = "considering"
    trialist = "trialist"
    adopter = "adopter"
    advocate = "advocate"
    lapsed = "lapsed"


class Tier(str, Enum):
    t1_grow = "t1_grow"
    t2_defend = "t2_defend"
    t3_develop = "t3_develop"
    t4_nurture = "t4_nurture"


class Access(str, Enum):
    open = "open"
    restricted = "restricted"
    no_see = "no_see"
    unknown = "unknown"


class EvidenceType(str, Enum):
    epidemiology = "epidemiology"
    guideline = "guideline"
    trial = "trial"
    rwe = "rwe"
    market = "market"
    pricing = "pricing"
    regulatory = "regulatory"
    competitor_claim = "competitor_claim"
    hcp_insight = "hcp_insight"
    patient_insight = "patient_insight"


class Driver(str, Enum):
    efficacy = "efficacy"
    safety = "safety"
    tolerability = "tolerability"
    convenience = "convenience"
    cost = "cost"
    evidence_strength = "evidence_strength"
    guideline = "guideline"
    access = "access"
    peer_use = "peer_use"
    support_services = "support_services"


class ClaimStrength(str, Enum):
    owned = "owned"
    contested = "contested"
    absent = "absent"


class MlrStatus(str, Enum):
    none = "none"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class Setting(str, Enum):
    hospital = "hospital"
    clinic = "clinic"
    both = "both"


class PersonaDerivation(str, Enum):
    survey = "survey"
    call_notes = "call_notes"
    social = "social"
    synthetic = "synthetic"


class CurveSource(str, Enum):
    prior = "prior"
    fitted = "fitted"


class UserRole(str, Enum):
    """The blueprint's Users & Roles table, plus two read-only access tiers
    (viewer, external_reviewer) it names but doesn't tabulate alongside the
    seven primary roles."""

    brand_manager = "brand_manager"
    brand_marketing_head = "brand_marketing_head"
    insights_analytics_lead = "insights_analytics_lead"
    sales_ops_field_excellence = "sales_ops_field_excellence"
    medical_mlr_reviewer = "medical_mlr_reviewer"
    market_country_lead = "market_country_lead"
    platform_admin = "platform_admin"
    viewer = "viewer"
    external_reviewer = "external_reviewer"


class ReviewDecisionType(str, Enum):
    approved = "approved"
    rejected = "rejected"


class ActionStatus(str, Enum):
    suggested = "suggested"
    accepted = "accepted"
    dismissed = "dismissed"
    done = "done"


class SourceCategory(str, Enum):
    """Drives the deterministic confidence heuristic in models/evidence.py
    (specs/m1-research.md). `other` is a defensive fallback not in the spec,
    for claims the extractor can't confidently bucket."""

    peer_reviewed_guideline_regulator = "peer_reviewed_guideline_regulator"
    audit_market_vendor = "audit_market_vendor"
    reputable_press = "reputable_press"
    vendor_blog = "vendor_blog"
    forum = "forum"
    other = "other"

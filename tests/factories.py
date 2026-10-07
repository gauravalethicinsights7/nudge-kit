"""Minimal valid instances of every entity, for schema/export tests."""

from datetime import date
from uuid import uuid4

from schemas.brand import Brand
from schemas.brand_plan import (
    BrandPlan,
    Forecast,
    ForecastScenario,
    Imperative,
    KeyIssue,
    KpiTree,
    MessageHouse,
    MessagePillar,
    Positioning,
    Situation,
)
from schemas.channel import Channel, ResponseCurve
from schemas.channel_fit import ChannelFit, FitComponents
from schemas.channel_plan import ChannelAllocation, ChannelPlan
from schemas.competitive import Competitor, MessageMap
from schemas.content import ContentBrief, ContentModule
from schemas.early_warning_signal import EarlyWarningSignal
from schemas.engagement import EngagementEvent
from schemas.enums import (
    Access,
    ActionStatus,
    ClaimStrength,
    CurveSource,
    Driver,
    EvidenceType,
    LifecycleStage,
    Market,
    MlrStatus,
    Origin,
    PersonaDerivation,
    Rung,
    Setting,
    Tier,
)
from schemas.evidence import Evidence
from schemas.hcp import HCP, AdoptionState, Consent, ExternalIds, Geo, Segment
from schemas.market_landscape import MarketLandscape, PatientFunnel
from schemas.measurement import (
    AssumptionCheck,
    AssumptionReview,
    KpiResult,
    LiftEstimate,
    Outcome,
    PriorUpdate,
    Scorecard,
)
from schemas.orchestration import Action, Escalation, JourneyRule, JourneyStepRule
from schemas.persona import JourneyMap, JourneyStep, Persona
from schemas.persona_assignment import PersonaAssignment
from schemas.research import ResearchGap
from schemas.run_record import RunRecord
from schemas.target_list import TargetList, TargetListEntry


def _prov_number(value: float = 1.0) -> dict:
    return dict(value=value, source="test", origin=Origin.estimated, as_of=date.today(), confidence=0.5)


def make_brand() -> Brand:
    return Brand(
        name="Brand S",
        molecule="semaglutide",
        indication="type 2 diabetes",
        market=Market.india,
        lifecycle_stage=LifecycleStage.launch,
        company="Test Pharma",
    )


def make_evidence(brand_id=None) -> Evidence:
    return Evidence(
        brand_id=brand_id or uuid4(),
        source="test",
        origin=Origin.external,
        as_of=date.today(),
        confidence=0.8,
        type=EvidenceType.market,
        claim="A claim under 500 chars.",
    )


def make_market_landscape(brand_id=None) -> MarketLandscape:
    return MarketLandscape(
        brand_id=brand_id or uuid4(),
        patient_funnel=PatientFunnel(
            prevalent=_prov_number(1000),
            diagnosed=_prov_number(800),
            treated=_prov_number(400),
            controlled=_prov_number(200),
        ),
        market_size=dict(value=1000.0, source="test", origin=Origin.estimated, as_of=date.today(), confidence=0.5, currency="INR"),
        growth_pct=_prov_number(5.0),
        paradigm={"text": "some paradigm", "evidence_ids": []},
        access_summary="mostly open access",
    )


def make_hcp() -> HCP:
    return HCP(
        external_ids=ExternalIds(crm_id="crm-1"),
        name_hash="hash123",
        specialty="endocrinologist",
        setting=Setting.clinic,
        geo=Geo(state="MH", city="Mumbai", city_tier="metro", territory_id="T1"),
        potential=_prov_number(100),
        brand_share=_prov_number(0.1),
        access=Access.open,
        consent=Consent(email=True),
    )


def make_segment(brand_id=None) -> Segment:
    return Segment(
        brand_id=brand_id or uuid4(),
        name="Metro endos",
        rule={"specialty": "endocrinologist"},
        tier=Tier.t1_grow,
        hcp_count=100,
        total_potential=1000.0,
        avg_share=0.1,
        target_share=0.15,
    )


def make_adoption_state(hcp_id=None, brand_id=None) -> AdoptionState:
    return AdoptionState(
        hcp_id=hcp_id or uuid4(),
        brand_id=brand_id or uuid4(),
        rung=Rung.aware,
        entered_on=date.today(),
        p_move_up=0.2,
    )


def make_persona(brand_id=None) -> Persona:
    return Persona(
        brand_id=brand_id or uuid4(),
        name="Evidence purist",
        drivers_ranked=list(Driver),  # a full ranking is required
        barriers_by_rung={
            Rung.aware: ["generic quality doubt"],
            Rung.considering: ["wants trial data"],
            Rung.trialist: ["titration uncertainty"],
        },
        share_of_universe=0.3,
        share_of_potential=0.4,
        derivation=PersonaDerivation.synthetic,
        assumption=True,
    )


def make_journey_map(brand_id=None) -> JourneyMap:
    return JourneyMap(
        brand_id=brand_id or uuid4(),
        steps=[
            JourneyStep(
                from_rung=Rung.aware,
                to_rung=Rung.considering,
                job="evaluate evidence",
                barrier="quality doubt",
                proof="bioequivalence data",
                exit_signal="detail_requested",
            )
        ],
    )


def make_competitor(brand_id=None) -> Competitor:
    return Competitor(
        brand_id=brand_id or uuid4(),
        competitor_brand="Ozempic",
        company="Novo Nordisk",
    )


def make_message_map(brand_id=None) -> MessageMap:
    return MessageMap(
        brand_id=brand_id or uuid4(),
        grid=[{"driver": Driver.cost, "brand": "Brand S", "strength": ClaimStrength.contested}],
    )


def make_channel() -> Channel:
    return Channel(
        channel_ref="rep_visit",
        name="Field rep visit",
        unit="call",
        curve=ResponseCurve(**{"lambda": 0.5, "alpha": 1.5, "gamma": 4, "source": CurveSource.prior}),
    )


def make_run_record() -> RunRecord:
    return RunRecord(module="test", inputs_hash="abc123", model="claude-sonnet-5")


def make_research_gap(brand_id=None) -> ResearchGap:
    return ResearchGap(
        brand_id=brand_id or uuid4(),
        block="disease_patient_flow",
        question="What is the prevalence of the disease/condition this brand treats?",
        best_confidence=0.2,
        reason="low_confidence",
    )


def make_target_list(brand_id=None, segment_id=None) -> TargetList:
    return TargetList(
        brand_id=brand_id or uuid4(),
        segment_id=segment_id or uuid4(),
        entries=[
            TargetListEntry(
                hcp_id=uuid4(), rank=1, opportunity_score=1.5, reachability=0.8, reason="test reason"
            )
        ],
    )


def make_persona_assignment(hcp_id=None, brand_id=None, persona_id=None) -> PersonaAssignment:
    return PersonaAssignment(
        hcp_id=hcp_id or uuid4(),
        brand_id=brand_id or uuid4(),
        persona_id=persona_id or uuid4(),
        confidence=0.75,
    )


def make_early_warning_signal(brand_id=None) -> EarlyWarningSignal:
    return EarlyWarningSignal(
        brand_id=brand_id or uuid4(),
        type="generic_entry",
        detection_rule="A new generic semaglutide product receives DCGI approval in India.",
        affected_segments=["T1 consulting physicians"],
    )


def make_brand_plan(brand_id=None) -> BrandPlan:
    brand_id = brand_id or uuid4()
    key_issue_ids = [uuid4() for _ in range(4)]
    key_issues = [
        KeyIssue(
            id=key_issue_ids[i],
            statement=f"Key issue {i}",
            barrier="generic quality doubt",
            revenue_at_stake=_prov_number(1_000_000.0) | {"currency": "INR"},
            evidence_ids=[uuid4()],
        )
        for i in range(4)
    ]
    return BrandPlan(
        brand_id=brand_id,
        situation=Situation(summary="Situation summary", key_facts=[{"text": "fact", "evidence_ids": [uuid4()]}]),
        key_issues=key_issues,
        imperatives=[
            Imperative(
                id=uuid4(),
                title="Win first GLP-1 starts",
                key_issue_ids=[key_issue_ids[0]],
                from_rung=Rung.aware,
                to_rung=Rung.considering,
            )
        ]
        * 3,
        positioning=Positioning(
            target="Consulting physicians",
            frame_of_reference="GLP-1 therapies",
            point_of_difference="Best patient support for persistence",
            driver=Driver.support_services,
            reasons_to_believe=[{"text": "reason", "evidence_ids": [uuid4()]}],
        ),
        message_house=MessageHouse(
            core="Core message",
            pillars=[
                MessagePillar(driver=Driver.support_services, message="p1", proofs=[uuid4()]),
                MessagePillar(driver=Driver.cost, message="p2", proofs=[uuid4()]),
                MessagePillar(driver=Driver.evidence_strength, message="p3", proofs=[uuid4()]),
            ],
        ),
        kpi_tree=KpiTree(leading=[{"name": "reach"}], lagging=[{"name": "nrx"}]),
        forecast=Forecast(
            base=ForecastScenario(delta_nrx=100.0, revenue=_prov_number(1_000_000.0) | {"currency": "INR"}),
            upside=ForecastScenario(delta_nrx=120.0, revenue=_prov_number(1_200_000.0) | {"currency": "INR"}),
            downside=ForecastScenario(delta_nrx=80.0, revenue=_prov_number(800_000.0) | {"currency": "INR"}),
        ),
    )


def make_channel_fit(brand_id=None, segment_id=None) -> ChannelFit:
    return ChannelFit(
        brand_id=brand_id or uuid4(),
        segment_id=segment_id or uuid4(),
        channel_id="rep_visit",
        fit_score=0.7,
        components=FitComponents(affinity=0.8, access=0.6, stage_fit=0.7, content_fit=0.5),
    )


def make_channel_plan(brand_id=None, segment_id=None) -> ChannelPlan:
    segment_id = segment_id or uuid4()
    return ChannelPlan(
        brand_id=brand_id or uuid4(),
        allocations={
            segment_id: {
                "rep_visit": ChannelAllocation(
                    touches_per_month=4.0, spend=_prov_number(1000.0) | {"currency": "INR"}, share_of_budget=0.6
                )
            }
        },
    )


def make_content_module(brand_id=None) -> ContentModule:
    return ContentModule(
        brand_id=brand_id or uuid4(),
        name="Titration support brochure",
        channel_refs=["rep_visit", "e_detailing"],
        driver=Driver.support_services,
        claim="Structured titration support improves persistence.",
        format="brochure",
        mlr_status=MlrStatus.approved,
    )


def make_content_brief(brand_id=None) -> ContentBrief:
    return ContentBrief(
        brand_id=brand_id or uuid4(),
        driver=Driver.efficacy,
        channel="email",
        format="email",
        claim_needed="Approved efficacy claim for email",
        reason="no approved content module found for this persona/channel/driver",
    )


def make_journey_rule(brand_id=None, segment_id=None, persona_id=None) -> JourneyRule:
    return JourneyRule(
        brand_id=brand_id or uuid4(),
        segment_id=segment_id or uuid4(),
        persona_id=persona_id or uuid4(),
        entry_criteria={"tier": "t1_grow"},
        steps=[
            JourneyStepRule(channel="rep_visit", content_ref="content-1", wait_days=0),
            JourneyStepRule(channel="whatsapp", content_ref=None, wait_days=2),
        ],
        escalation=[Escalation(signal="detail_requested", action="escalate_to_rep")],
        exit_signal="first_rx",
    )


def make_action(brand_id=None, hcp_id=None) -> Action:
    return Action(
        brand_id=brand_id or uuid4(),
        hcp_id=hcp_id or uuid4(),
        channel="rep_visit",
        content_ref="content-1",
        suggested_date=date.today(),
        reason="Highest affinity channel for this persona; not yet suppressed.",
        score=1.23,
        action_status=ActionStatus.suggested,
    )


def make_engagement_event(brand_id=None, hcp_id=None) -> EngagementEvent:
    return EngagementEvent(
        brand_id=brand_id or uuid4(),
        hcp_id=hcp_id or uuid4(),
        channel="whatsapp",
        depth="opened",
        occurred_at=date.today(),
        period="2026-01",
    )


def make_outcome(brand_id=None, hcp_id=None) -> Outcome:
    return Outcome(
        brand_id=brand_id or uuid4(),
        hcp_id=hcp_id or uuid4(),
        period="2026-01",
        engagement_index=42.0,
        rung=Rung.aware,
        nrx=3.0,
        trx=10.0,
    )


def make_scorecard(brand_id=None) -> Scorecard:
    return Scorecard(
        brand_id=brand_id or uuid4(),
        period="2026-01",
        kpis=[KpiResult(name="engagement_index", category="engagement", actual=42.0, plan=50.0, variance=-8.0, rag="amber")],
    )


def make_lift_estimate(brand_id=None) -> LiftEstimate:
    return LiftEstimate(
        brand_id=brand_id or uuid4(),
        test_name="Metro endos pilot",
        effect=1.5,
        ci_low=0.5,
        ci_high=2.5,
        method="did",
    )


def make_prior_update(brand_id=None) -> PriorUpdate:
    return PriorUpdate(
        brand_id=brand_id or uuid4(),
        prior_type="rung_transition",
        key="aware",
        period="2026-01",
        before=0.15,
        after=0.18,
    )


def make_assumption_review(brand_id=None) -> AssumptionReview:
    return AssumptionReview(
        brand_id=brand_id or uuid4(),
        period="2026-01",
        items=[AssumptionCheck(assumption="persistence_6m", held=True, planned_value=1.0, actual_value=0.95)],
    )

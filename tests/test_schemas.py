from schemas.registry import ENTITIES
from tests import factories

FACTORY_BY_NAME = {
    "Brand": factories.make_brand,
    "Evidence": factories.make_evidence,
    "MarketLandscape": factories.make_market_landscape,
    "HCP": factories.make_hcp,
    "Segment": factories.make_segment,
    "AdoptionState": factories.make_adoption_state,
    "Persona": factories.make_persona,
    "JourneyMap": factories.make_journey_map,
    "Competitor": factories.make_competitor,
    "MessageMap": factories.make_message_map,
    "Channel": factories.make_channel,
    "RunRecord": factories.make_run_record,
    "ResearchGap": factories.make_research_gap,
    "TargetList": factories.make_target_list,
    "PersonaAssignment": factories.make_persona_assignment,
    "EarlyWarningSignal": factories.make_early_warning_signal,
    "BrandPlan": factories.make_brand_plan,
    "ChannelFit": factories.make_channel_fit,
    "ChannelPlan": factories.make_channel_plan,
    "ContentModule": factories.make_content_module,
    "ContentBrief": factories.make_content_brief,
    "JourneyRule": factories.make_journey_rule,
    "Action": factories.make_action,
    "EngagementEvent": factories.make_engagement_event,
    "Outcome": factories.make_outcome,
    "Scorecard": factories.make_scorecard,
    "LiftEstimate": factories.make_lift_estimate,
    "PriorUpdate": factories.make_prior_update,
    "AssumptionReview": factories.make_assumption_review,
}


def test_registry_covers_every_factory():
    registry_names = {e.__name__ for e in ENTITIES}
    assert registry_names == set(FACTORY_BY_NAME)


def test_every_entity_builds_and_round_trips_json():
    for entity_cls in ENTITIES:
        instance = FACTORY_BY_NAME[entity_cls.__name__]()
        assert isinstance(instance, entity_cls)
        dumped = instance.model_dump_json()
        restored = entity_cls.model_validate_json(dumped)
        assert restored == instance

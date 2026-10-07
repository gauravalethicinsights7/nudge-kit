"""Single list of every top-level entity, used by the JSON-schema exporter and tests."""

from schemas.brand import Brand
from schemas.brand_plan import BrandPlan
from schemas.channel import Channel
from schemas.channel_fit import ChannelFit
from schemas.channel_plan import ChannelPlan
from schemas.competitive import Competitor, MessageMap
from schemas.content import ContentBrief, ContentModule
from schemas.early_warning_signal import EarlyWarningSignal
from schemas.engagement import EngagementEvent
from schemas.evidence import Evidence
from schemas.hcp import HCP, AdoptionState, Segment
from schemas.market_landscape import MarketLandscape
from schemas.measurement import AssumptionReview, LiftEstimate, Outcome, PriorUpdate, Scorecard
from schemas.orchestration import Action, JourneyRule
from schemas.persona import JourneyMap, Persona
from schemas.persona_assignment import PersonaAssignment
from schemas.research import ResearchGap
from schemas.run_record import RunRecord
from schemas.target_list import TargetList

ENTITIES = [
    Brand,
    Evidence,
    MarketLandscape,
    HCP,
    Segment,
    AdoptionState,
    Persona,
    JourneyMap,
    Competitor,
    MessageMap,
    Channel,
    RunRecord,
    ResearchGap,
    TargetList,
    PersonaAssignment,
    EarlyWarningSignal,
    BrandPlan,
    ChannelFit,
    ChannelPlan,
    ContentModule,
    ContentBrief,
    JourneyRule,
    Action,
    EngagementEvent,
    Outcome,
    Scorecard,
    LiftEstimate,
    PriorUpdate,
    AssumptionReview,
]

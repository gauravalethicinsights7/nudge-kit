// Hand-written TS mirrors of the Pydantic entities in /schemas (NUDGE engine).
// Not codegen — kept intentionally close to what the UI actually renders.

export type Status = "draft" | "approved" | "superseded";
export type Market = "india" | "us";
export type LifecycleStage = "pre_launch" | "launch" | "growth" | "mature" | "loe";
export type Rung = "unaware" | "aware" | "considering" | "trialist" | "adopter" | "advocate" | "lapsed";
export type Tier = "t1_grow" | "t2_defend" | "t3_develop" | "t4_nurture";
export type Access = "open" | "restricted" | "no_see" | "unknown";
export type Driver =
  | "efficacy" | "safety" | "tolerability" | "convenience" | "cost"
  | "evidence_strength" | "guideline" | "access" | "peer_use" | "support_services";
export type ClaimStrength = "owned" | "contested" | "absent";
export type MlrStatus = "none" | "submitted" | "approved" | "rejected";
export type Origin = "external" | "internal" | "estimated";
export type ActionStatus = "suggested" | "accepted" | "dismissed" | "done";
export type CurveSource = "prior" | "fitted";
export type Rag = "green" | "amber" | "red";

export interface Prov {
  source: string;
  origin: Origin;
  as_of: string;
  confidence: number;
}

export interface ProvNumber extends Prov {
  value: number;
  low: number | null;
  high: number | null;
}

export interface ProvMoney extends ProvNumber {
  currency: string;
}

export interface Base {
  id: string;
  tenant_id: string | null;
  created_at: string;
  updated_at: string;
  status: Status;
  version: number;
}

export interface Brand extends Base {
  name: string;
  molecule: string;
  indication: string;
  market: Market;
  lifecycle_stage: LifecycleStage;
  company: string;
  price_band: string | null;
  notes: string | null;
}

export interface EvidencedText {
  text: string;
  evidence_ids: string[];
}

export interface Evidence extends Base, Prov {
  brand_id: string;
  type: string;
  claim: string;
  quote: string | null;
  source_url: string | null;
  publisher: string | null;
  published_date: string | null;
  mlr_status: MlrStatus;
}

export interface MarketLandscape extends Base {
  brand_id: string;
  patient_funnel: {
    prevalent: ProvNumber | null;
    diagnosed: ProvNumber | null;
    treated: ProvNumber | null;
    controlled: ProvNumber | null;
  } | null;
  market_size: ProvMoney | null;
  growth_pct: ProvNumber | null;
  paradigm: EvidencedText | null;
  access_summary: string | null;
  unmet_needs: string[];
  key_facts: EvidencedText[];
}

export interface ResearchGap extends Base {
  brand_id: string;
  block: string;
  question: string;
  best_confidence: number;
  reason: "unanswered" | "low_confidence";
  notes: string | null;
}

export interface Segment extends Base {
  brand_id: string;
  name: string;
  tier: Tier;
  hcp_count: number;
  total_potential: number;
  avg_share: number;
  target_share: number;
  intent: string | null;
  mode: "hcp_level" | "segment_only";
}

export interface AdoptionState extends Base {
  hcp_id: string;
  brand_id: string;
  rung: Rung;
  entered_on: string;
  p_move_up: number;
  measured: boolean;
  rung_confidence: number;
}

export interface TargetListEntry {
  hcp_id: string;
  rank: number;
  opportunity_score: number;
  reachability: number;
  reason: string;
}

export interface TargetList extends Base {
  brand_id: string;
  segment_id: string;
  entries: TargetListEntry[];
}

export interface Persona extends Base {
  brand_id: string;
  name: string;
  beliefs: string[];
  drivers_ranked: Driver[];
  barriers_by_rung: Record<string, string[]>;
  channel_affinity: Record<string, number>;
  share_of_universe: number;
  share_of_potential: number;
  derivation: "survey" | "call_notes" | "social" | "synthetic";
  assumption: boolean;
  confidence: number;
}

export interface JourneyStep {
  from_rung: Rung;
  to_rung: Rung;
  job: string;
  barrier: string;
  proof: string;
  lead_channels: string[];
  exit_signal: string;
}

export interface JourneyMap extends Base {
  brand_id: string;
  persona_id: string | null;
  steps: JourneyStep[];
}

export interface CompetitorClaim {
  driver: Driver;
  text: string;
  strength: ClaimStrength;
  evidence_id: string;
  requires_mlr_comparative: boolean;
}

export interface Competitor extends Base {
  brand_id: string;
  competitor_brand: string;
  company: string;
  claims: CompetitorClaim[];
  price: ProvMoney | null;
}

export interface MessageGridCell {
  driver: Driver;
  brand: string;
  strength: ClaimStrength;
}

export interface Whitespace {
  driver: Driver;
  personas: string[];
  rationale: string;
}

export interface MessageMap extends Base {
  brand_id: string;
  grid: MessageGridCell[];
  whitespace: Whitespace[];
  parity_risks: string[];
  threats: string[];
}

export interface EarlyWarningSignal extends Base {
  brand_id: string;
  type: string;
  detection_rule: string;
  affected_segments: string[];
}

export interface KeyIssue {
  id: string;
  statement: string;
  barrier: string;
  revenue_at_stake: ProvMoney;
}

export interface Imperative {
  id: string;
  title: string;
  key_issue_ids: string[];
  from_rung: Rung;
  to_rung: Rung;
}

export interface Positioning {
  target: string;
  frame_of_reference: string;
  point_of_difference: string;
  driver: Driver;
  reasons_to_believe: EvidencedText[];
}

export interface MessagePillar {
  driver: Driver;
  message: string;
  proofs: string[];
}

export interface MessageHouse {
  core: string;
  pillars: MessagePillar[];
  by_persona: Record<string, string>;
}

export interface Objective {
  imperative_id: string;
  metric: string;
  baseline: number;
  target: number;
  due: string;
}

export interface ForecastAssumption {
  name: string;
  value: number;
  confidence: number;
}

export interface ForecastScenario {
  delta_nrx: number;
  revenue: ProvMoney;
  roi: number | null;
  assumptions: ForecastAssumption[];
}

export interface Forecast {
  base: ForecastScenario;
  upside: ForecastScenario;
  downside: ForecastScenario;
}

export interface BudgetLine {
  imperative_id: string | null;
  channel_id: string | null;
  amount: ProvMoney;
  marginal_roi: number | null;
  position: "under" | "efficient" | "saturated" | null;
}

export interface Budget {
  lines: BudgetLine[];
  placeholder: boolean;
}

export interface ComplianceFlag {
  item: string;
  rule_id: string;
  severity: string;
}

export interface Situation {
  summary: string;
  key_facts: EvidencedText[];
}

export interface BrandPlan extends Base {
  brand_id: string;
  plan_horizon_months: number;
  situation: Situation;
  key_issues: KeyIssue[];
  imperatives: Imperative[];
  positioning: Positioning;
  message_house: MessageHouse;
  objectives: Objective[];
  forecast: Forecast;
  budget: Budget;
  compliance_flags: ComplianceFlag[];
}

export interface ResponseCurve {
  lambda: number;
  alpha: number;
  gamma: number;
  beta: number | null;
  source: CurveSource;
}

export interface Channel extends Base {
  channel_ref: string;
  name: string;
  unit: string;
  unit_cost: ProvMoney | null;
  capacity: number | null;
  curve: ResponseCurve;
}

export interface FitComponents {
  affinity: number;
  access: number;
  stage_fit: number;
  content_fit: number;
}

export interface ChannelFit extends Base {
  brand_id: string;
  segment_id: string;
  persona_id: string | null;
  channel_id: string;
  fit_score: number;
  components: FitComponents;
}

export interface ChannelAllocation {
  touches_per_month: number;
  spend: ProvMoney;
  share_of_budget: number;
}

export interface ChannelPlan extends Base {
  brand_id: string;
  allocations: Record<string, Record<string, ChannelAllocation>>;
}

export interface ContentModule extends Base {
  brand_id: string;
  name: string;
  channel_refs: string[];
  driver: Driver;
  claim: string;
  format: string;
  mlr_status: MlrStatus;
  on_label: boolean;
  is_comparative: boolean;
  comparative_approved: boolean;
  patient_directed: boolean;
  exceeds_pack_limit: boolean;
}

export interface ContentBrief {
  brand_id: string;
  driver: Driver;
  persona_id: string | null;
  channel: string;
  format: string;
  claim_needed: string;
  reason: string;
}

export interface JourneyStepRule {
  channel: string;
  content_ref: string | null;
  wait_days: number;
  condition: string | null;
}

export interface Escalation {
  signal: string;
  action: string;
}

export interface JourneyRule extends Base {
  brand_id: string;
  segment_id: string;
  persona_id: string;
  entry_criteria: Record<string, unknown>;
  steps: JourneyStepRule[];
  escalation: Escalation[];
  exit_signal: string;
}

export interface Action extends Base {
  brand_id: string;
  hcp_id: string;
  channel: string;
  content_ref: string | null;
  suggested_date: string;
  reason: string;
  score: number;
  action_status: ActionStatus;
}

export interface Outcome extends Base {
  brand_id: string;
  hcp_id: string | null;
  segment_id: string | null;
  period: string;
  engagement_index: number;
  rung: Rung | null;
  nrx: number | null;
  trx: number | null;
}

export interface KpiResult {
  name: string;
  category: "activity" | "engagement" | "outcome";
  actual: number;
  plan: number | null;
  variance: number | null;
  rag: Rag | null;
}

export interface Scorecard extends Base {
  brand_id: string;
  period: string;
  kpis: KpiResult[];
}

export interface LiftEstimate extends Base {
  brand_id: string;
  test_name: string;
  effect: number;
  ci_low: number;
  ci_high: number;
  method: "did" | "counterfactual_trend";
}

export interface PriorUpdate extends Base {
  brand_id: string;
  prior_type: "rung_transition" | "curve_param" | "fit_weight";
  key: string;
  period: string;
  before: number;
  after: number;
}

export interface AssumptionCheck {
  assumption: string;
  held: boolean;
  planned_value: number;
  actual_value: number;
}

export interface AssumptionReview extends Base {
  brand_id: string;
  period: string;
  items: AssumptionCheck[];
}

export interface RunRecord extends Base {
  module: string;
  model: string;
  tokens_in: number;
  tokens_out: number;
  cost: number;
  duration_ms: number;
  error: string | null;
}

export interface SystemStatus {
  anthropic_configured: boolean;
  serper_configured: boolean;
  run_budget_usd: number;
}

export interface UploadInfo {
  kind: string;
  path?: string;
  row_count: number | null;
}

export interface PackChannel {
  id: string;
  name: string;
  unit: string;
  unit_cost: number | null;
  requires_consent: boolean;
  consent_field: string | null;
}

export interface ComplianceRule {
  id: string;
  rule: string;
  applies_to: string[];
  severity: string;
}

export interface Pack {
  market: Market;
  currency: string;
  channels: PackChannel[];
  frequency_caps: Record<string, number>;
  suppress_after: number;
  compliance_rules: ComplianceRule[];
  signals: string[];
  priors: {
    rung_transition_monthly: Record<string, number>;
    persistence_6m_default: number | null;
    benchmark_confidence: number;
  };
  kpis: { leading: string[]; lagging: string[] };
}

export interface ApprovalCount {
  entity_type: string;
  draft_count: number;
}

export interface DraftRow {
  id: string;
  status: Status;
  created_at: string;
}

export interface ReviewDecision {
  id: string;
  brand_id: string;
  entity_type: string;
  object_id: string;
  decision: "approved" | "rejected";
  comment: string | null;
  reviewer_user_id: string;
  created_at: string;
}

export type JobStatus = "pending" | "running" | "done" | "failed";

export interface Job {
  id: string;
  brand_id: string;
  module: string;
  status: JobStatus;
  message: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export const USER_ROLES = [
  "brand_manager",
  "brand_marketing_head",
  "insights_analytics_lead",
  "sales_ops_field_excellence",
  "medical_mlr_reviewer",
  "market_country_lead",
  "platform_admin",
  "viewer",
  "external_reviewer",
] as const;

export type UserRole = (typeof USER_ROLES)[number];

export interface Tenant {
  id: string;
  name: string;
  created_at: string;
}

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: UserRole;
  created_at: string;
}

export interface UserBrandAccess {
  id: string;
  user_id: string;
  brand_id: string;
  granted_at: string;
}

export interface PilotPair {
  hcp_a: string;
  hcp_b: string;
  distance: number;
}

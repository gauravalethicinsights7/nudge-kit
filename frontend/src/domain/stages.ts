import type { UserRole } from "../api/types";

/* The pipeline, as one declaration.
 *
 * NUDGE answers one question: where should the next rupee and the next rep
 * visit go to get the most patients started and kept on therapy? Each stage
 * is one step toward that answer, so each one carries the decision it drives
 * — not just a title.
 *
 * `approverRoles` is DERIVED from the real permission matrix rather than
 * written by hand: the server is what actually enforces approval, and a
 * header naming an approver the server disagrees with would be a lie of
 * exactly the kind this product exists to remove. Keep APPROVE_PERMISSIONS
 * in state/AuthContext.tsx as the single source of truth.
 */

export interface Stage {
  id: string;
  /** Short index shown in the rail: M1, M4, D … */
  ix: string;
  label: string;
  group: string;
  /** Route segment under /brands/:brandId/ */
  route: string;
  /** Stages whose output this one reads. Drives the "built on drafts" warning. */
  upstream: string[];
  /** Entity types this stage produces — the approval unit. */
  entityTypes: string[];
  /** The decision this page helps a brand team make. */
  decision: string;
  /** What the page shows, in one line. */
  shows: string;
}

export const STAGES: Stage[] = [
  {
    id: "overview",
    ix: "—",
    label: "Command centre",
    group: "Start",
    route: "",
    upstream: [],
    entityTypes: [],
    decision: "Know in 30 seconds where the plan stands and what needs you.",
    shows: "Progress across the eight modules, approvals waiting, and the plan in one line.",
  },
  {
    id: "data",
    ix: "D",
    label: "Data Hub",
    group: "Start",
    route: "data-hub",
    upstream: [],
    entityTypes: [],
    decision: "Decide what to connect next — the engine never fills a missing input with a guess.",
    shows: "Each data source, whether it is loaded, and what connecting it unlocks.",
  },
  {
    id: "m1",
    ix: "M1",
    label: "Market Landscape",
    group: "Understand the market",
    route: "market-landscape",
    upstream: [],
    entityTypes: ["market_landscape", "research_gap"],
    decision: "Establish the facts every later decision rests on — and admit what is still unknown.",
    shows: "Patient funnel, market size, unmet needs, and the evidence behind each.",
  },
  {
    id: "evidence",
    ix: "E",
    label: "Evidence Library",
    group: "Understand the market",
    route: "evidence",
    upstream: ["m1"],
    entityTypes: [],
    decision: "Challenge any claim in the plan by going to its source.",
    shows: "Every claim with its source, origin, as-of date and confidence.",
  },
  {
    id: "m2",
    ix: "M2",
    label: "Segments & Targeting",
    group: "Know the doctors",
    route: "segments",
    upstream: ["m1"],
    entityTypes: ["segment", "adoption_state", "target_list"],
    decision: "Decide which doctors get the most effort — scoring value separately from movability.",
    shows: "Tiers, rep-capacity check, and a target list with a reason per doctor.",
  },
  {
    id: "m3",
    ix: "M3",
    label: "Personas & Journeys",
    group: "Know the doctors",
    route: "personas",
    upstream: ["m1", "m2"],
    entityTypes: ["persona", "journey_map", "persona_assignment"],
    decision: "Decide what to say to each kind of doctor, and where they are stuck.",
    shows: "Personas with drivers, barriers by journey step, and channel affinity.",
  },
  {
    id: "m4",
    ix: "M4",
    label: "Competitive Map",
    group: "Know the doctors",
    route: "competitive",
    upstream: ["m1"],
    entityTypes: ["competitor", "message_map", "early_warning_signal"],
    decision: "Find the message that matters to doctors and that no competitor owns.",
    shows: "Claim grid by driver, open space, and early-warning signals.",
  },
  {
    id: "m5",
    ix: "M5",
    label: "Brand Plan",
    group: "Decide the plan",
    route: "brand-plan",
    upstream: ["m1", "m2", "m3", "m4"],
    entityTypes: ["brand_plan"],
    decision: "Commit to what the brand will do, for whom, with what message — and what it should deliver.",
    shows: "Key issues ranked by money at stake, positioning, message house, forecast.",
  },
  {
    id: "m6",
    ix: "M6",
    label: "Channel Planner",
    group: "Decide the plan",
    route: "channel-planner",
    upstream: ["m2", "m3", "m5"],
    entityTypes: ["channel", "channel_fit", "channel_plan"],
    decision: "Decide where the next rupee keeps the most patients on therapy, within capacity and the law.",
    shows: "Current vs recommended spend, response curves, and channel fit by segment.",
  },
  {
    id: "m7",
    ix: "M7",
    label: "Orchestration & NBA",
    group: "Act and learn",
    route: "orchestration",
    upstream: ["m5", "m6"],
    entityTypes: ["journey_rule", "action"],
    decision: "Turn the plan into rules a CRM can run and a ranked to-do for every doctor.",
    shows: "Journey rules, the weekly next-best-action feed, and the guardrails applied.",
  },
  {
    id: "m8",
    ix: "M8",
    label: "Measurement",
    group: "Act and learn",
    route: "measurement",
    upstream: ["m5"],
    entityTypes: ["outcome", "scorecard", "lift_estimate", "prior_update", "assumption_review"],
    decision: "Prove what the plan caused, and carry the measured rates into the next cycle.",
    shows: "Scorecard vs plan, causal lift, and the assumptions that held or failed.",
  },
  {
    id: "appr",
    ix: "✓",
    label: "Approvals Inbox",
    group: "Governance",
    route: "approvals",
    upstream: [],
    entityTypes: [],
    decision: "Sign off each module before later modules rely on it. A machine never approves its own work.",
    shows: "Every pending draft, who owns it, and the full decision history.",
  },
];

export const STAGE_GROUPS = [...new Set(STAGES.map((s) => s.group))];

export function stageById(id: string): Stage | undefined {
  return STAGES.find((s) => s.id === id);
}

export function stageByRoute(route: string): Stage | undefined {
  return STAGES.find((s) => s.route === route);
}

/** Roles the server would actually accept an approval from, for this stage. */
export function approverRolesFor(
  stage: Stage,
  permissions: Record<UserRole, string[]>,
): UserRole[] {
  if (!stage.entityTypes.length) return [];
  return (Object.keys(permissions) as UserRole[]).filter(
    (role) =>
      role !== "platform_admin" &&
      stage.entityTypes.some((t) => permissions[role].includes(t)),
  );
}

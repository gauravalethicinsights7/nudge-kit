import { useParams, Link } from "react-router-dom";
import { ArrowRight, CircleDot } from "lucide-react";
import {
  useBrand, useMarketLandscape, useSegments, usePersonas, useCompetitors,
  useBrandPlan, useChannelPlan, useActions, useScorecard, useApprovals,
} from "../api/hooks";
import { SkeletonKpiRow } from "../components/Skeleton";
import {
  AccentCallout,
  Badge,
  BulletList,
  Card,
  MetricStat,
  SectionHeading,
} from "../components/shared/ui";

function ModuleCard({ to, title, ready, detail }: { to: string; title: string; ready: boolean; detail: string }) {
  return (
    <Link
      to={to}
      className="card"
      style={{
        display: "block",
        margin: 0,
        borderLeft: `3px solid ${ready ? "var(--emerald)" : "var(--border-strong)"}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text-1)" }}>{title}</span>
        <Badge color={ready ? "emerald" : "neutral"}>{ready ? "Has data" : "Not run"}</Badge>
      </div>
      <p style={{ margin: "8px 0 0", fontSize: 12.5, color: "var(--text-3)", lineHeight: 1.6 }}>{detail}</p>
    </Link>
  );
}

const STEPS: { key: string; title: string; to: string; ready: (d: Record<string, unknown>) => boolean }[] = [
  { key: "landscape", title: "Market landscape", to: "market-landscape", ready: (d) => !!d.landscape },
  { key: "segments", title: "Segments", to: "segments", ready: (d) => !!(d.segments as unknown[])?.length },
  { key: "personas", title: "Personas", to: "personas", ready: (d) => !!(d.personas as unknown[])?.length },
  { key: "competitive", title: "Competitive map", to: "competitive", ready: (d) => !!(d.competitors as unknown[])?.length },
  { key: "plan", title: "Brand plan", to: "brand-plan", ready: (d) => !!d.plan },
  { key: "channel", title: "Channel plan", to: "channel-planner", ready: (d) => !!d.channelPlan },
  { key: "actions", title: "Orchestration", to: "orchestration", ready: (d) => !!(d.actions as unknown[])?.length },
  { key: "measure", title: "Measurement", to: "measurement", ready: (d) => !!d.scorecard },
];

export function BrandOverview() {
  const { brandId } = useParams();
  const { data: brand } = useBrand(brandId);
  const { data: landscape, isLoading: landscapeLoading } = useMarketLandscape(brandId);
  const { data: segments, isLoading: segmentsLoading } = useSegments(brandId);
  const { data: personas } = usePersonas(brandId);
  const { data: competitors } = useCompetitors(brandId);
  const { data: plan } = useBrandPlan(brandId);
  const { data: channelPlan } = useChannelPlan(brandId);
  const { data: actions } = useActions(brandId);
  const { data: scorecard } = useScorecard(brandId);
  const { data: approvals, isLoading: approvalsLoading } = useApprovals(brandId);

  const pendingApprovals = approvals?.reduce((sum, a) => sum + a.draft_count, 0) ?? 0;
  const topSegment = segments?.length
    ? [...segments].sort((a, b) => b.total_potential - a.total_potential)[0]
    : null;

  const stepData = { landscape, segments, personas, competitors, plan, channelPlan, actions, scorecard };
  const completedSteps = STEPS.filter((s) => s.ready(stepData));
  const nextStep = STEPS.find((s) => !s.ready(stepData));
  const isLoading = landscapeLoading || segmentsLoading || approvalsLoading;
  const progressPct = Math.round((completedSteps.length / STEPS.length) * 100);

  return (
    <div>
      <SectionHeading
        eyebrow="Command centre"
        title={brand?.name ?? "Brand"}
        sub="Understand the market → Know the doctors → Decide the plan → Act and learn."
        right={
          nextStep ? (
            <Link to={nextStep.to} className="btn btn-gold">
              Continue: {nextStep.title}
              <ArrowRight size={14} style={{ marginLeft: 6, verticalAlign: "-2px" }} />
            </Link>
          ) : undefined
        }
      />

      {isLoading ? (
        <SkeletonKpiRow count={4} />
      ) : (
        <div className="grid grid-4" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <MetricStat
              label="Segments"
              value={segments?.length ?? 0}
              sub={topSegment ? `Largest: ${topSegment.name}` : undefined}
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Personas" value={personas?.length ?? 0} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat
              label="Pending approvals"
              value={pendingApprovals}
              sub={pendingApprovals > 0 ? "Awaiting review" : "All clear"}
              tone={pendingApprovals > 0 ? "red" : "emerald"}
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Actions (NBA)" value={actions?.length ?? 0} tone="gold" />
          </Card>
        </div>
      )}

      <Card style={{ borderLeft: "3px solid var(--navy)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 14 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              fontSize: 10.5,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.07em",
              color: "var(--navy)",
            }}
          >
            <CircleDot size={12} />
            Plan progress
          </div>
          <Badge color={progressPct === 100 ? "emerald" : "gold"}>
            {completedSteps.length} of {STEPS.length} modules
          </Badge>
        </div>

        <div
          style={{
            height: 8,
            borderRadius: 999,
            background: "var(--bg-raised)",
            overflow: "hidden",
            marginBottom: 16,
          }}
        >
          <div
            style={{
              width: `${progressPct}%`,
              height: "100%",
              borderRadius: 999,
              background: progressPct === 100 ? "var(--emerald)" : "var(--gold)",
            }}
          />
        </div>

        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-1)", lineHeight: 1.5, marginBottom: 14 }}>
          {nextStep
            ? `Next up: ${nextStep.title}.`
            : "All eight modules have data. The brand plan and activation plan are ready for review."}
        </div>

        {completedSteps.length > 0 && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {completedSteps.map((s) => (
              <Badge key={s.key} color="emerald">{s.title}</Badge>
            ))}
            {STEPS.filter((s) => !s.ready(stepData)).map((s) => (
              <Badge key={s.key} color="neutral">{s.title}</Badge>
            ))}
          </div>
        )}
      </Card>

      <h2 className="section-title">Understand the market</h2>
      <div className="grid grid-2" style={{ marginBottom: 22 }}>
        <ModuleCard
          to={`/brands/${brandId}/market-landscape`}
          title="Market Landscape (M1)"
          ready={!!landscape}
          detail={landscape ? "Patient funnel, market size and unmet needs computed." : "Needs ANTHROPIC_API_KEY and SERPER_API_KEY."}
        />
        <ModuleCard
          to={`/brands/${brandId}/data-hub`}
          title="Data Hub"
          ready={false}
          detail="Upload HCPs, content library, engagement and sales data."
        />
      </div>

      <h2 className="section-title">Know the doctors</h2>
      <div className="grid grid-3" style={{ marginBottom: 22 }}>
        <ModuleCard
          to={`/brands/${brandId}/segments`}
          title="Segments & Targeting (M2)"
          ready={!!segments?.length}
          detail={segments?.length ? `${segments.length} segments tiered by potential.` : "Upload HCPs, then run M2."}
        />
        <ModuleCard
          to={`/brands/${brandId}/personas`}
          title="Personas & Journeys (M3)"
          ready={!!personas?.length}
          detail={personas?.length ? `${personas.length} personas with drivers and barriers.` : "Needs ANTHROPIC_API_KEY."}
        />
        <ModuleCard
          to={`/brands/${brandId}/competitive`}
          title="Competitive Map (M4)"
          ready={!!competitors?.length}
          detail={competitors?.length ? `${competitors.length} competitors mapped.` : "Needs ANTHROPIC_API_KEY and SERPER_API_KEY."}
        />
      </div>

      <h2 className="section-title">Decide the plan</h2>
      <div className="grid grid-2" style={{ marginBottom: 22 }}>
        <ModuleCard
          to={`/brands/${brandId}/brand-plan`}
          title="Brand Plan (M5)"
          ready={!!plan}
          detail={plan ? `${plan.key_issues.length} key issues, ${plan.imperatives.length} imperatives.` : "Needs ANTHROPIC_API_KEY."}
        />
        <ModuleCard
          to={`/brands/${brandId}/channel-planner`}
          title="Channel Planner (M6)"
          ready={!!channelPlan}
          detail={channelPlan ? "Budget allocated across channels." : "Run after segments and personas exist."}
        />
      </div>

      <h2 className="section-title">Act and learn</h2>
      <div className="grid grid-2" style={{ marginBottom: 22 }}>
        <ModuleCard
          to={`/brands/${brandId}/orchestration`}
          title="Orchestration & NBA (M7)"
          ready={!!actions?.length}
          detail={actions?.length ? `${actions.length} actions in this run's feed.` : "Upload a content library, then run."}
        />
        <ModuleCard
          to={`/brands/${brandId}/measurement`}
          title="Measurement (M8)"
          ready={!!scorecard}
          detail={scorecard ? `Scorecard for ${scorecard.period}.` : "Run after a brand plan exists."}
        />
      </div>

      {pendingApprovals > 0 && (
        <AccentCallout tone="gold" label="Governance">
          <BulletList
            items={[
              `${pendingApprovals} draft objects are awaiting review.`,
              "Downstream modules read approved objects only in production.",
            ]}
            size={12.5}
          />
        </AccentCallout>
      )}
    </div>
  );
}

import { useParams, Link } from "react-router-dom";
import { ArrowRight, CircleDot, ShieldAlert } from "lucide-react";
import {
  useMarketLandscape, useSegments, usePersonas, useCompetitors,
  useBrandPlan, useChannelPlan, useActions, useScorecard, useApprovals,
} from "../api/hooks";
import { SkeletonKpiRow } from "../components/Skeleton";
import { StageHeader } from "../components/shared/StageHeader";
import { Figure, HowCalculated } from "../components/shared/provenance";
import { AccentCallout, Badge, Card, MicroLabel } from "../components/shared/ui";
import { STAGES, stageById } from "../domain/stages";
import { fmtMoney, fmtMoneyExact } from "../lib/format";

/** Which stages actually produced something. Separate from the rail's
 *  "nothing waiting for sign-off" — this is the one place that queries each
 *  module, so it is the only place that can honestly say "has data". */
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

const PIPELINE = ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"];

export function BrandOverview() {
  const { brandId } = useParams();
  const { data: landscape, isLoading: landscapeLoading } = useMarketLandscape(brandId);
  const { data: segments, isLoading: segmentsLoading } = useSegments(brandId);
  const { data: personas } = usePersonas(brandId);
  const { data: competitors } = useCompetitors(brandId);
  const { data: plan } = useBrandPlan(brandId);
  const { data: channelPlan } = useChannelPlan(brandId);
  const { data: actions } = useActions(brandId);
  const { data: scorecard } = useScorecard(brandId);
  const { data: approvals, isLoading: approvalsLoading } = useApprovals(brandId);

  const ready: Record<string, boolean> = {
    m1: !!landscape,
    m2: !!segments?.length,
    m3: !!personas?.length,
    m4: !!competitors?.length,
    m5: !!plan,
    m6: !!channelPlan,
    m7: !!actions?.length,
    m8: !!scorecard,
  };

  const pendingApprovals = approvals?.reduce((sum, a) => sum + a.draft_count, 0) ?? 0;
  const topSegment = segments?.length
    ? [...segments].sort((a, b) => b.total_potential - a.total_potential)[0]
    : null;

  const done = PIPELINE.filter((id) => ready[id]);
  const nextId = PIPELINE.find((id) => !ready[id]);
  const next = nextId ? stageById(nextId) : undefined;
  const progressPct = Math.round((done.length / PIPELINE.length) * 100);
  const isLoading = landscapeLoading || segmentsLoading || approvalsLoading;

  // The one-line answer to "what is this plan worth, and how sure are we?"
  const baseRevenue = plan?.forecast.base.revenue;
  const spreadPct = plan
    ? ((plan.forecast.upside.revenue.value - plan.forecast.downside.revenue.value) /
        Math.max(plan.forecast.base.revenue.value, 1)) * 100
    : 0;
  const blockers = plan?.compliance_flags.filter((f) => f.severity === "block") ?? [];

  return (
    <div>
      <StageHeader
        stageId="overview"
        right={
          next ? (
            <Link to={next.route} className="btn btn-gold">
              Continue: {next.label}
              <ArrowRight size={14} style={{ marginLeft: 6, verticalAlign: "-2px" }} />
            </Link>
          ) : undefined
        }
      />

      {blockers.length > 0 && (
        <AccentCallout
          tone="red"
          label="This plan cannot be activated yet"
          icon={<ShieldAlert size={12} />}
          style={{ marginBottom: 18 }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {blockers.map((f, i) => (
              <div key={i} style={{ fontSize: 13, lineHeight: 1.55 }}>{f.item}</div>
            ))}
          </div>
        </AccentCallout>
      )}

      {isLoading ? (
        <SkeletonKpiRow count={4} />
      ) : (
        <div className="grid grid-4" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Plan worth / year"
              value={baseRevenue ? fmtMoney(baseRevenue.value, baseRevenue.currency) : "–"}
              unit={baseRevenue?.currency}
              tone="gold"
              sub={
                baseRevenue
                  ? `±${spreadPct.toFixed(0)}% between downside and upside`
                  : "Run the brand plan to forecast"
              }
              calc={
                baseRevenue ? (
                  <HowCalculated
                    formula="Doctors in journeys → doctors trying → patients on therapy → revenue at the monthly price over twelve months."
                    steps={[
                      { label: "Downside", value: fmtMoneyExact(plan!.forecast.downside.revenue.value, plan!.forecast.downside.revenue.currency) },
                      { label: "Base", value: fmtMoneyExact(plan!.forecast.base.revenue.value, plan!.forecast.base.revenue.currency) },
                      { label: "Upside", value: fmtMoneyExact(plan!.forecast.upside.revenue.value, plan!.forecast.upside.revenue.currency) },
                    ]}
                    result={`${fmtMoneyExact(baseRevenue.value, baseRevenue.currency)} ${baseRevenue.currency}`}
                    note="Open the Brand Plan to see which assumptions carry this number and which still need a test."
                  />
                ) : undefined
              }
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Doctors prioritised"
              value={(segments?.reduce((n, s) => n + s.hcp_count, 0) ?? 0).toLocaleString()}
              sub={topSegment ? `Largest: ${topSegment.name}` : undefined}
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Actions this week"
              value={(actions?.length ?? 0).toLocaleString()}
              sub="Ranked, guardrail-checked, ready for the CRM"
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Waiting on you"
              value={pendingApprovals.toLocaleString()}
              tone={pendingApprovals > 0 ? "red" : "emerald"}
              sub={pendingApprovals > 0 ? "Drafts needing sign-off" : "Nothing outstanding"}
            />
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
            {done.length} of {PIPELINE.length} modules
          </Badge>
        </div>

        <div style={{ height: 8, borderRadius: 999, background: "var(--bg-raised)", overflow: "hidden", marginBottom: 16 }}>
          <div
            style={{
              width: `${progressPct}%`,
              height: "100%",
              borderRadius: 999,
              background: progressPct === 100 ? "var(--emerald)" : "var(--gold)",
            }}
          />
        </div>

        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-1)", lineHeight: 1.5, marginBottom: 6 }}>
          {next ? `Next up: ${next.label}.` : "All eight modules have data. The plan is ready for review."}
        </div>
        <div style={{ fontSize: 12.5, color: "var(--text-3)", lineHeight: 1.6, marginBottom: 14 }}>
          {next ? next.decision : "Every module has produced output. What remains is sign-off and activation."}
        </div>

        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {PIPELINE.map((id) => {
            const s = stageById(id)!;
            return (
              <Badge key={id} color={ready[id] ? "emerald" : "neutral"}>
                {s.ix} {s.label}
              </Badge>
            );
          })}
        </div>
      </Card>

      {[...new Set(STAGES.filter((s) => PIPELINE.includes(s.id)).map((s) => s.group))].map((group) => (
        <div key={group}>
          <h2 className="section-title">{group}</h2>
          <div className="grid grid-3" style={{ marginBottom: 22 }}>
            {STAGES.filter((s) => s.group === group && PIPELINE.includes(s.id)).map((s) => (
              <ModuleCard
                key={s.id}
                to={`/brands/${brandId}/${s.route}`}
                title={`${s.label} (${s.ix})`}
                ready={ready[s.id]}
                detail={s.decision}
              />
            ))}
          </div>
        </div>
      ))}

      <Card>
        <MicroLabel>How to read every number in here</MicroLabel>
        <div style={{ fontSize: 13, lineHeight: 1.7, color: "var(--text-2)", maxWidth: "72ch" }}>
          The model writes and explains; it never does the arithmetic. Every figure comes from a
          fixed formula you can open, and carries a chip saying whether it is{" "}
          <strong>measured</strong> from real data, <strong>estimated</strong> from proxies, or an{" "}
          <strong>assumption</strong> someone stated. Where two sources disagree, both are kept as a
          range rather than averaged. Where nothing reached the confidence bar, the gap is left
          visible instead of filled with a guess.
        </div>
      </Card>
    </div>
  );
}

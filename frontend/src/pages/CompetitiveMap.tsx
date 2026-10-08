import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Radar, Swords, Target } from "lucide-react";
import { useCompetitors, useEarlyWarningSignals, useMessageMap, useRunM4, useSystemStatus } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { ChartCard } from "../components/charts/ChartCard";
import { HeatmapChart } from "../components/charts/HeatmapChart";
import { SkeletonText } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  AccentCallout,
  AvatarInitials,
  Badge,
  Card,
  EmptyState,
  Field,
  MetricStat,
  Pill,
} from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";
import type { BadgeColor } from "../components/shared/ui";

const STRENGTH_VALUE: Record<string, number> = { owned: 1, contested: 0.5, absent: 0 };
const STRENGTH_LABEL: Record<number, string> = { 1: "owned", 0.5: "contested", 0: "absent" };
const STRENGTH_COLOR: Record<string, BadgeColor> = {
  owned: "emerald",
  contested: "amber",
  absent: "neutral",
};

export function CompetitiveMap() {
  const { brandId } = useParams();
  const { data: competitors, isLoading } = useCompetitors(brandId);
  const { data: messageMap } = useMessageMap(brandId);
  const { data: ews } = useEarlyWarningSignals(brandId);
  const { data: status } = useSystemStatus();
  const runM4 = useRunM4(brandId);
  const [openCompetitor, setOpenCompetitor] = useState<string | null>(null);
  const [strengthFilter, setStrengthFilter] = useState<string>("all");

  const disabledReason = !status?.anthropic_configured
    ? "ANTHROPIC_API_KEY is not configured"
    : !status?.serper_configured
    ? "SERPER_API_KEY is not configured — web research is unavailable"
    : null;

  const heatmapData = useMemo(
    () =>
      messageMap?.grid.map((cell) => ({
        driver: cell.driver,
        brand: cell.brand,
        strength: STRENGTH_VALUE[cell.strength] ?? 0,
      })) ?? [],
    [messageMap],
  );

  const competitor = competitors?.find((c) => c.id === openCompetitor) ?? null;
  const visibleClaims =
    competitor?.claims.filter((c) => strengthFilter === "all" || c.strength === strengthFilter) ?? [];
  const driverCount = new Set(messageMap?.grid.map((c) => c.driver)).size;
  const heatHeight = Math.max(220, driverCount * 36);

  return (
    <div>
      <StageHeader
        stageId="m4"
                right={
          <RunButton
            label="Run M4"
            onRun={() => runM4.mutate({})}
            isPending={runM4.isPending}
            disabledReason={disabledReason}
            error={runM4.error}
          />
        }
      />

      {!isLoading && !!competitors?.length && (
        <div className="grid grid-3" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Competitors tracked" value={competitors.length} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Whitespace drivers" value={messageMap?.whitespace.length ?? 0} tone="gold" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Early-warning signals" value={ews?.length ?? 0} />
          </Card>
        </div>
      )}

      <Card title="Competitors" sub="Select a competitor to review its full claim set">
        {isLoading ? (
          <SkeletonText lines={5} />
        ) : !competitors?.length ? (
          <EmptyState
            icon={<Swords size={28} strokeWidth={1.6} />}
            title="No competitors yet"
            sub="Run M4 once both API keys are configured to discover and map competitors."
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}>
            {competitors.map((c) => {
              const owned = c.claims.filter((x) => x.strength === "owned").length;
              return (
                <button
                  key={c.id}
                  onClick={() => {
                    setStrengthFilter("all");
                    setOpenCompetitor(c.id);
                  }}
                  style={{
                    all: "unset",
                    cursor: "pointer",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: 16,
                    display: "flex",
                    gap: 12,
                    alignItems: "flex-start",
                    background: "var(--bg-surface)",
                  }}
                >
                  <AvatarInitials text={c.competitor_brand} size={34} />
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 700, color: "var(--text-1)" }}>
                      {c.competitor_brand}
                    </div>
                    <div style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 2 }}>{c.company}</div>
                    <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
                      <Badge color="navySoft">{c.claims.length} claims</Badge>
                      {owned > 0 && <Badge color="emerald">{owned} owned</Badge>}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </Card>

      <ChartCard
        title="Message grid"
        subtitle="Claim strength by driver × brand — owned, contested, or absent"
        height={heatHeight}
        isEmpty={!heatmapData.length}
        emptyMessage="No message map yet."
      >
        <HeatmapChart
          data={heatmapData}
          x="brand"
          y="driver"
          value="strength"
          height={heatHeight}
          colorScale={["#fef2f2", "#10b981"]}
          cellLabel={(v) => STRENGTH_LABEL[v] ?? String(v)}
        />
      </ChartCard>

      <div style={{ height: 22 }} />

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <Card title="Whitespace" sub="Drivers no competitor credibly owns" style={{ margin: 0 }}>
          {messageMap?.whitespace.length ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {messageMap.whitespace.map((w, i) => (
                <AccentCallout key={i} tone="gold" label={w.driver} icon={<Target size={12} />}>
                  {w.rationale}
                </AccentCallout>
              ))}
            </div>
          ) : (
            <EmptyState icon={<Target size={24} strokeWidth={1.6} />} sub="No whitespace identified yet." />
          )}
        </Card>

        <Card title="Early-warning signals" sub="What to watch, and the rule that triggers it" style={{ margin: 0 }}>
          {ews?.length ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {ews.map((s) => (
                <div key={s.id} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <Badge color="blue">{s.type}</Badge>
                  <span style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{s.detection_rule}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={<Radar size={24} strokeWidth={1.6} />} sub="No signals defined yet." />
          )}
        </Card>
      </div>

      <DetailModal
        open={!!competitor}
        onClose={() => setOpenCompetitor(null)}
        eyebrow={competitor?.company}
        title={competitor?.competitor_brand ?? ""}
        width={860}
      >
        {competitor && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {["all", "owned", "contested", "absent"].map((s) => (
                <Pill key={s} active={strengthFilter === s} onClick={() => setStrengthFilter(s)}>
                  {s === "all" ? `All (${competitor.claims.length})` : s}
                </Pill>
              ))}
            </div>
            <Field label={`Claims (${visibleClaims.length})`}>
              <div style={{ display: "flex", flexDirection: "column" }}>
                {visibleClaims.map((claim, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "12px 0",
                      borderBottom: i === visibleClaims.length - 1 ? "none" : "1px solid var(--border)",
                    }}
                  >
                    <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{claim.text}</div>
                    <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                      <Badge color="navySoft">{claim.driver}</Badge>
                      <Badge color={STRENGTH_COLOR[claim.strength] ?? "neutral"}>{claim.strength}</Badge>
                    </div>
                  </div>
                ))}
                {!visibleClaims.length && <EmptyState sub="No claims match this filter." />}
              </div>
            </Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

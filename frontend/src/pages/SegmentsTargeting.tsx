import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Layers } from "lucide-react";
import { useAdoptionStates, useRunM2, useSegments, useTargetLists, useUploads } from "../api/hooks";
import { DataTable } from "../components/DataTable";
import { RunButton } from "../components/RunButton";
import { StatusBadge } from "../components/Badge";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import { SkeletonKpiRow, SkeletonTable } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import { StageHeader } from "../components/shared/StageHeader";
import { Figure, HowCalculated, ProvenanceChip } from "../components/shared/provenance";
import { Badge, Card, EmptyState, Field, MicroLabel, TableWrap } from "../components/shared/ui";
import type { Segment } from "../api/types";

// Field-force arithmetic from the market pack's call-planning norms. Exposed
// as constants (and surfaced in the UI) rather than buried, because the whole
// capacity answer swings on them.
const WORKING_DAYS = 22;
const CALLS_PER_DAY = 9;
const SHARE_OF_TIME = 0.3;
const T1_CALLS_PER_MONTH = 3;

const columns = [
  { key: "name", header: "Segment", render: (s: Segment) => <span style={{ fontWeight: 600 }}>{s.name}</span> },
  { key: "tier", header: "Tier", render: (s: Segment) => <Badge color="navySoft">{s.tier}</Badge> },
  { key: "hcps", header: "HCPs", render: (s: Segment) => s.hcp_count.toLocaleString() },
  { key: "potential", header: "Potential", render: (s: Segment) => s.total_potential.toFixed(0) },
  {
    key: "share",
    header: "Share (avg → target)",
    render: (s: Segment) => `${(s.avg_share * 100).toFixed(1)}% → ${(s.target_share * 100).toFixed(1)}%`,
  },
  {
    key: "mode",
    header: "Basis",
    render: (s: Segment) => (
      <ProvenanceChip
        grade={s.mode === "hcp_level" ? "measured" : "estimated"}
        prov={{
          source:
            s.mode === "hcp_level"
              ? "Doctor-level file matched to the HCP database"
              : "Sized from specialty, setting and city tier — no doctor file connected",
        }}
        compact
      />
    ),
  },
  { key: "status", header: "Status", render: (s: Segment) => <StatusBadge status={s.status} /> },
];

const RUNG_ORDER = ["unaware", "aware", "considering", "trialist", "adopter", "advocate", "lapsed"];

export function SegmentsTargeting() {
  const { brandId } = useParams();
  const { data: segments, isLoading } = useSegments(brandId);
  const { data: adoptionStates } = useAdoptionStates(brandId);
  const { data: targetLists } = useTargetLists(brandId);
  const { data: uploads } = useUploads(brandId);
  const runM2 = useRunM2(brandId);
  const [targetShare, setTargetShare] = useState(0.05);
  const [reps, setReps] = useState(400);
  const [openList, setOpenList] = useState<string | null>(null);

  const hasHcps = uploads?.some((u) => u.kind === "hcp_sample");
  const rungCounts = (adoptionStates ?? []).reduce<Record<string, number>>((acc, a) => {
    acc[a.rung] = (acc[a.rung] ?? 0) + 1;
    return acc;
  }, {});
  const rungData = RUNG_ORDER.filter((r) => rungCounts[r]).map((r) => ({ rung: r, count: rungCounts[r] }));

  const potentialByTier = useMemo(() => {
    if (!segments?.length) return [];
    const totals = new Map<string, number>();
    for (const s of segments) totals.set(s.tier, (totals.get(s.tier) ?? 0) + s.total_potential);
    return Array.from(totals.entries())
      .map(([tier, potential]) => ({ tier, potential }))
      .sort((a, b) => b.potential - a.potential);
  }, [segments]);

  // Can the field force actually deliver the plan? A target list nobody has
  // the capacity to call is the most common way a plan quietly fails.
  const capacity = useMemo(() => {
    const t1Doctors = (segments ?? [])
      .filter((s) => s.tier?.toLowerCase().startsWith("t1"))
      .reduce((n, s) => n + s.hcp_count, 0);
    const available = Math.round(reps * WORKING_DAYS * CALLS_PER_DAY * SHARE_OF_TIME);
    const required = t1Doctors * T1_CALLS_PER_MONTH;
    return { t1Doctors, available, required, gap: available - required };
  }, [segments, reps]);

  const list = targetLists?.find((t) => t.id === openList) ?? null;
  const hcpLevel = segments?.some((s) => s.mode === "hcp_level");

  return (
    <div>
      <StageHeader
        stageId="m2"
        right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Target share</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={targetShare}
                onChange={(e) => setTargetShare(Number(e.target.value))}
                style={{ width: 90 }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
              <RunButton
                label="Run M2"
                onRun={() => runM2.mutate({ target_share: targetShare })}
                isPending={runM2.isPending}
                error={runM2.error}
                primary
              />
              {!hasHcps && (
                <span style={{ fontSize: 11, color: "var(--text-3)" }}>
                  No doctor file — segment-only sizing will run
                </span>
              )}
            </div>
          </div>
        }
      />

      {isLoading ? (
        <SkeletonKpiRow count={4} />
      ) : (
        <div className="grid grid-4" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <Figure label="Segments" value={segments?.length ?? 0} />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Doctors scored"
              value={(adoptionStates?.length ?? 0).toLocaleString()}
              grade={hcpLevel ? "measured" : "estimated"}
              prov={{
                source: hcpLevel
                  ? "Doctor-level file matched to the HCP database"
                  : "Segment-only sizing — connect a doctor file for named lists",
              }}
            />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure label="Target lists" value={targetLists?.length ?? 0} tone="gold" />
          </Card>
          <Card style={{ margin: 0 }}>
            <Figure
              label="Rungs observed"
              value={Object.keys(rungCounts).length}
              sub="of 7 on the adoption journey"
            />
          </Card>
        </div>
      )}

      {capacity.t1Doctors > 0 && (
        <Card
          style={{
            borderLeft: `3px solid ${capacity.gap < 0 ? "var(--red)" : "var(--emerald)"}`,
          }}
        >
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            {capacity.gap < 0 ? (
              <AlertTriangle size={16} style={{ color: "var(--red)", flexShrink: 0, marginTop: 2 }} />
            ) : (
              <CheckCircle2 size={16} style={{ color: "var(--emerald)", flexShrink: 0, marginTop: 2 }} />
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <MicroLabel>Rep capacity check</MicroLabel>
              <div style={{ fontSize: 14.5, fontWeight: 700, color: "var(--text-1)", marginBottom: 4 }}>
                {capacity.gap < 0
                  ? `Short by ${Math.abs(capacity.gap).toLocaleString()} calls a month to cover tier 1.`
                  : `Field force covers tier 1 with ${capacity.gap.toLocaleString()} calls a month spare.`}
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-3)", lineHeight: 1.6 }}>
                {capacity.gap < 0
                  ? "Raise the tier-1 bar, add reps, or move tier-1 follow-ups to digital. The plan cannot be delivered as it stands."
                  : "The call plan is deliverable at the current field-force size."}
              </div>

              <div style={{ display: "flex", gap: 24, marginTop: 14, flexWrap: "wrap" }}>
                <Figure
                  label="Calls available"
                  value={capacity.available.toLocaleString()}
                  unit="/ month"
                />
                <Figure
                  label="Calls required"
                  value={capacity.required.toLocaleString()}
                  unit="/ month"
                  tone={capacity.gap < 0 ? "red" : "navy"}
                />
                <Figure
                  label="Tier-1 doctors"
                  value={capacity.t1Doctors.toLocaleString()}
                />
                <div className="form-row" style={{ margin: 0, alignSelf: "flex-end" }}>
                  <label>Reps</label>
                  <input
                    type="number"
                    value={reps}
                    onChange={(e) => setReps(Number(e.target.value))}
                    style={{ width: 90 }}
                  />
                </div>
              </div>

              <HowCalculated
                formula="Calls available = reps × working days × calls per day × share of time on this brand. Calls required = tier-1 doctors × calls per doctor per month."
                steps={[
                  { label: "Reps", value: reps.toLocaleString() },
                  { label: "Working days a month", value: WORKING_DAYS },
                  { label: "Calls a day", value: CALLS_PER_DAY },
                  { label: "Share of time on this brand", value: `${SHARE_OF_TIME * 100}%` },
                  { label: "→ Calls available", value: capacity.available.toLocaleString() },
                  { label: "Tier-1 doctors", value: capacity.t1Doctors.toLocaleString() },
                  { label: "Calls per tier-1 doctor", value: T1_CALLS_PER_MONTH },
                  { label: "→ Calls required", value: capacity.required.toLocaleString() },
                ]}
                result={`${capacity.gap >= 0 ? "+" : ""}${capacity.gap.toLocaleString()} calls a month`}
                note="Working days, calls a day and share of time are market-pack norms. Change the rep count above to test a different field-force size."
              />
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-2" style={{ marginBottom: 22 }}>
        <ChartCard
          title="Potential by tier"
          subtitle="Total suitable patients controlled, summed per tier"
          isEmpty={!potentialByTier.length}
        >
          <BarChart data={potentialByTier} x="tier" y="potential" valueFormatter={(v) => v.toFixed(0)} />
        </ChartCard>
        <ChartCard
          title="Adoption journey"
          subtitle="Doctors by step — never heard through to champion"
          isEmpty={!rungData.length}
          emptyMessage="Connect a doctor file and re-run M2 to place doctors on the journey."
        >
          <BarChart data={rungData} x="rung" y="count" horizontal valueFormatter={(v) => v.toFixed(0)} />
        </ChartCard>
      </div>

      <Card title="Segments" sub={`${segments?.length ?? 0} segments, ranked by tier and potential`}>
        {isLoading ? (
          <SkeletonTable rows={5} cols={7} />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <DataTable
              rows={segments ?? []}
              columns={columns}
              rowKey={(s) => s.id}
              emptyMessage="No segments yet — upload a doctor file in the Data Hub, then run M2."
            />
          </div>
        )}
      </Card>

      <Card
        title="Target lists"
        sub="Ranked doctors per segment, each with the reason they are on the list"
      >
        {targetLists?.length ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}>
            {targetLists.map((tl) => (
              <button
                key={tl.id}
                onClick={() => setOpenList(tl.id)}
                style={{
                  all: "unset",
                  cursor: "pointer",
                  borderLeft: "3px solid var(--navy)",
                  background: "var(--bg-raised)",
                  borderRadius: "var(--radius-sm)",
                  padding: "14px 16px",
                }}
              >
                <Figure
                  label={`Segment ${tl.segment_id.slice(0, 8)}`}
                  value={tl.entries.length.toLocaleString()}
                  sub="doctors ranked by opportunity"
                />
              </button>
            ))}
          </div>
        ) : (
          <EmptyState icon={<Layers size={24} strokeWidth={1.6} />} sub="No target lists yet." />
        )}
      </Card>

      <DetailModal
        open={!!list}
        onClose={() => setOpenList(null)}
        eyebrow="Target list"
        title={list ? `Segment ${list.segment_id.slice(0, 8)} — ${list.entries.length} doctors` : ""}
        width={900}
      >
        {list && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <HowCalculated
              label="How the ranking works"
              formula="Opportunity = potential × target share × movability × reachability × eligibility. Value and movability are scored separately, because the biggest prescribers are often the hardest to move."
              note="A doctor with fewer patients can outrank a bigger one when they are far easier to shift. The reason column shows which factor drove each placement."
            />
            <Field label="Top 25 by opportunity score">
              <TableWrap minWidth={640}>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Doctor</th>
                    <th>Opportunity</th>
                    <th>Reachability</th>
                    <th>Why they are here</th>
                  </tr>
                </thead>
                <tbody>
                  {list.entries.slice(0, 25).map((e) => (
                    <tr key={e.hcp_id}>
                      <td>{e.rank}</td>
                      <td>{e.hcp_id.slice(0, 8)}</td>
                      <td className="tabular" style={{ fontWeight: 600 }}>
                        {e.opportunity_score.toFixed(1)}
                      </td>
                      <td className="tabular">{e.reachability.toFixed(2)}</td>
                      <td style={{ fontSize: 11.5 }}>{e.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

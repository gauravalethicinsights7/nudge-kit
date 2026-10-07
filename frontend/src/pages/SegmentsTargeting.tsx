import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Layers } from "lucide-react";
import { useAdoptionStates, useRunM2, useSegments, useTargetLists, useUploads } from "../api/hooks";
import { DataTable } from "../components/DataTable";
import { RunButton } from "../components/RunButton";
import { StatusBadge } from "../components/Badge";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import { SkeletonKpiRow, SkeletonTable } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  Badge,
  Card,
  EmptyState,
  Field,
  MetricStat,
  SectionHeading,
  TableWrap,
} from "../components/shared/ui";
import type { Segment } from "../api/types";

const columns = [
  { key: "name", header: "Segment", render: (s: Segment) => <span style={{ fontWeight: 600 }}>{s.name}</span> },
  { key: "tier", header: "Tier", render: (s: Segment) => <Badge color="navySoft">{s.tier}</Badge> },
  { key: "hcps", header: "HCPs", render: (s: Segment) => s.hcp_count },
  { key: "potential", header: "Potential", render: (s: Segment) => s.total_potential.toFixed(0) },
  {
    key: "share",
    header: "Share (avg → target)",
    render: (s: Segment) => `${(s.avg_share * 100).toFixed(1)}% → ${(s.target_share * 100).toFixed(1)}%`,
  },
  { key: "mode", header: "Mode", render: (s: Segment) => s.mode },
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

  const list = targetLists?.find((t) => t.id === openList) ?? null;

  return (
    <div>
      <SectionHeading
        eyebrow="M2 · Know the doctors"
        title="Segments & Targeting"
        sub="Tiers HCPs by potential, share and reachability — or sizes segments directly when no HCP list exists."
        right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Target share</label>
              <input type="number" step="0.01" min="0" max="1" value={targetShare} onChange={(e) => setTargetShare(Number(e.target.value))} style={{ width: 90 }} />
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
                  No HCP file uploaded — segment-only mode will run
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
            <MetricStat label="Segments" value={segments?.length ?? 0} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="HCPs scored" value={adoptionStates?.length ?? 0} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Target lists" value={targetLists?.length ?? 0} tone="gold" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Rungs observed" value={Object.keys(rungCounts).length} sub="of 7 possible" />
          </Card>
        </div>
      )}

      <div className="grid grid-2" style={{ marginBottom: 22 }}>
        <ChartCard title="Potential by tier" subtitle="Total addressable potential summed per tier" isEmpty={!potentialByTier.length}>
          <BarChart data={potentialByTier} x="tier" y="potential" valueFormatter={(v) => v.toFixed(0)} />
        </ChartCard>
        <ChartCard
          title="Adoption rung distribution"
          subtitle="HCP count by rung, unaware → lapsed"
          isEmpty={!rungData.length}
          emptyMessage="Run M2 in HCP-level mode to see rung distribution."
        >
          <BarChart data={rungData} x="rung" y="count" horizontal valueFormatter={(v) => v.toFixed(0)} />
        </ChartCard>
      </div>

      <Card title="Segments" sub={`${segments?.length ?? 0} segments ranked by tier and potential`}>
        {isLoading ? (
          <SkeletonTable rows={5} cols={7} />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <DataTable
              rows={segments ?? []}
              columns={columns}
              rowKey={(s) => s.id}
              emptyMessage="No segments yet — upload HCPs in the Data Hub, then run M2."
            />
          </div>
        )}
      </Card>

      <Card title="Target lists" sub="Ranked HCPs per segment — select a list for the full ranking">
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
                <MetricStat
                  label={`Segment ${tl.segment_id.slice(0, 8)}`}
                  value={tl.entries.length}
                  sub="HCPs ranked"
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
        title={list ? `Segment ${list.segment_id.slice(0, 8)} — ${list.entries.length} HCPs` : ""}
        width={880}
      >
        {list && (
          <Field label="Top 25 by opportunity score">
            <TableWrap minWidth={620}>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>HCP</th>
                  <th>Opportunity</th>
                  <th>Reachability</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {list.entries.slice(0, 25).map((e) => (
                  <tr key={e.hcp_id}>
                    <td>{e.rank}</td>
                    <td>{e.hcp_id.slice(0, 8)}</td>
                    <td>{e.opportunity_score.toFixed(1)}</td>
                    <td>{e.reachability.toFixed(2)}</td>
                    <td style={{ fontSize: 11.5 }}>{e.reason}</td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          </Field>
        )}
      </DetailModal>
    </div>
  );
}

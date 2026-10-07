import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Radio } from "lucide-react";
import { useChannelFits, useChannelPlan, useChannels, usePersonas, useRunM6, useSegments } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { ChartCard } from "../components/charts/ChartCard";
import { HeatmapChart } from "../components/charts/HeatmapChart";
import { StackedBarChart } from "../components/charts/StackedBarChart";
import { SkeletonTable } from "../components/Skeleton";
import { Badge, Card, EmptyState, MetricStat, SectionHeading, TableWrap } from "../components/shared/ui";

const MAX_HEATMAP_SEGMENTS = 20;

export function ChannelPlanner() {
  const { brandId } = useParams();
  const { data: channels, isLoading } = useChannels(brandId);
  const { data: channelFits } = useChannelFits(brandId);
  const { data: channelPlan } = useChannelPlan(brandId);
  const { data: segments } = useSegments(brandId);
  const { data: personas } = usePersonas(brandId);
  const runM6 = useRunM6(brandId);

  const [budgetEnvelope, setBudgetEnvelope] = useState(500000);
  const [repCount, setRepCount] = useState<number | "">(50);

  const disabledReason = !segments?.length
    ? "No segments — run M2 first"
    : !personas?.length
    ? "No personas — run M3 first"
    : null;

  const segmentName = useMemo(() => new Map(segments?.map((s) => [s.id, s.name]) ?? []), [segments]);

  const fitHeatmapData = useMemo(() => {
    if (!channelFits?.length) return [];
    const avgBySegment = new Map<string, { sum: number; n: number }>();
    for (const f of channelFits) {
      const agg = avgBySegment.get(f.segment_id) ?? { sum: 0, n: 0 };
      agg.sum += f.fit_score;
      agg.n += 1;
      avgBySegment.set(f.segment_id, agg);
    }
    const topSegmentIds = new Set(
      Array.from(avgBySegment.entries())
        .sort((a, b) => b[1].sum / b[1].n - a[1].sum / a[1].n)
        .slice(0, MAX_HEATMAP_SEGMENTS)
        .map(([id]) => id),
    );
    return channelFits
      .filter((f) => topSegmentIds.has(f.segment_id))
      .map((f) => ({
        segment: segmentName.get(f.segment_id) ?? f.segment_id.slice(0, 8),
        channel: f.channel_id,
        fit_score: f.fit_score,
      }));
  }, [channelFits, segmentName]);

  const totalSegmentsWithFits = new Set(channelFits?.map((f) => f.segment_id)).size;
  const totalSegmentsWithAllocations = channelPlan ? Object.keys(channelPlan.allocations).length : 0;

  const allocationData = useMemo(() => {
    if (!channelPlan) return [];
    const totalSpendBySegment = Object.entries(channelPlan.allocations).map(
      ([segmentId, byChannel]) =>
        [segmentId, Object.values(byChannel).reduce((sum, a) => sum + a.spend.value, 0)] as const,
    );
    const topSegmentIds = totalSpendBySegment
      .sort((a, b) => b[1] - a[1])
      .slice(0, MAX_HEATMAP_SEGMENTS)
      .map(([id]) => id);
    const rows: { category: string; series: string; value: number }[] = [];
    for (const segmentId of topSegmentIds) {
      const byChannel = channelPlan.allocations[segmentId];
      for (const [channelId, alloc] of Object.entries(byChannel)) {
        rows.push({
          category: segmentName.get(segmentId) ?? segmentId.slice(0, 8),
          series: channelId,
          value: alloc.spend.value,
        });
      }
    }
    return rows;
  }, [channelPlan, segmentName]);

  const totalSpend = allocationData.reduce((n, r) => n + r.value, 0);
  const fitHeight = Math.max(220, MAX_HEATMAP_SEGMENTS * 26);

  return (
    <div>
      <SectionHeading
        eyebrow="M6 · Decide the plan"
        title="Channel Planner"
        sub="Fit scores per segment × channel, then an optimiser allocates budget and capacity to maximise response subject to caps and compliance."
        right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Budget envelope</label>
              <input type="number" value={budgetEnvelope} onChange={(e) => setBudgetEnvelope(Number(e.target.value))} style={{ width: 120 }} />
            </div>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Rep count</label>
              <input type="number" value={repCount} onChange={(e) => setRepCount(e.target.value === "" ? "" : Number(e.target.value))} style={{ width: 80 }} />
            </div>
            <RunButton
              label="Run M6"
              onRun={() => runM6.mutate({ budget_envelope: budgetEnvelope, rep_count: repCount === "" ? null : repCount })}
              isPending={runM6.isPending}
              disabledReason={disabledReason}
              error={runM6.error}
            />
          </div>
        }
      />

      <div className="grid grid-4" style={{ marginBottom: 22 }}>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Channels" value={channels?.length ?? 0} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Fit scores" value={channelFits?.length ?? 0} />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Segments allocated" value={totalSegmentsWithAllocations} tone="emerald" />
        </Card>
        <Card style={{ margin: 0 }}>
          <MetricStat label="Spend allocated" value={totalSpend ? totalSpend.toLocaleString() : "–"} tone="gold" />
        </Card>
      </div>

      <Card title={`Channels (${channels?.length ?? 0})`} sub="Unit economics and response curve per channel, from the market pack">
        {isLoading ? (
          <SkeletonTable rows={4} cols={5} />
        ) : channels?.length ? (
          <TableWrap minWidth={680}>
            <thead>
              <tr>
                <th>Channel</th>
                <th>Unit cost</th>
                <th>Capacity</th>
                <th>Curve (λ, α, γ)</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.name}</td>
                  <td>
                    {c.unit_cost ? `${c.unit_cost.value} ${c.unit_cost.currency}` : "–"}
                    {c.unit_cost && c.unit_cost.confidence < 0.5 ? (
                      <Badge color="amber" style={{ marginLeft: 6 }}>Low confidence</Badge>
                    ) : null}
                  </td>
                  <td>{c.capacity ?? "Uncapped"}</td>
                  <td>
                    {c.curve.lambda.toFixed(2)}, {c.curve.alpha.toFixed(2)}, {c.curve.gamma.toFixed(1)}
                  </td>
                  <td>
                    <Badge color="navySoft">{c.curve.source}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <EmptyState icon={<Radio size={24} strokeWidth={1.6} />} sub="No channels yet." />
        )}
      </Card>

      <ChartCard
        title="Channel fit"
        subtitle={
          totalSegmentsWithFits > MAX_HEATMAP_SEGMENTS
            ? `Top ${MAX_HEATMAP_SEGMENTS} of ${totalSegmentsWithFits} segments by average fit score × channel`
            : "Fit score by segment × channel"
        }
        height={fitHeight}
        isEmpty={!fitHeatmapData.length}
        emptyMessage="No channel fits yet."
      >
        <HeatmapChart
          data={fitHeatmapData}
          x="channel"
          y="segment"
          value="fit_score"
          height={fitHeight}
          cellLabel={(v) => v.toFixed(2)}
        />
      </ChartCard>

      <div style={{ height: 22 }} />

      <ChartCard
        title="Channel plan allocations"
        subtitle={
          totalSegmentsWithAllocations > MAX_HEATMAP_SEGMENTS
            ? `Top ${MAX_HEATMAP_SEGMENTS} of ${totalSegmentsWithAllocations} segments by total spend`
            : "Spend by channel per segment"
        }
        height={fitHeight}
        isEmpty={!allocationData.length}
        emptyMessage="No channel plan yet."
      >
        <StackedBarChart
          data={allocationData}
          category="category"
          series="series"
          value="value"
          horizontal
          height={fitHeight}
          valueFormatter={(v) => v.toLocaleString()}
        />
      </ChartCard>
    </div>
  );
}

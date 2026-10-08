import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BookOpen, HelpCircle } from "lucide-react";
import { useEvidence, useResearchGaps } from "../api/hooks";
import { DataTable } from "../components/DataTable";
import { ConfidenceBadge } from "../components/Badge";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import { SkeletonTable } from "../components/Skeleton";
import {
  AccentCallout,
  Badge,
  Card,
  EmptyState,
  MetricStat,
  Pill,
} from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";
import type { Evidence } from "../api/types";

const columns = [
  {
    key: "claim",
    header: "Claim",
    render: (e: Evidence) => (
      <span style={{ maxWidth: 460, display: "inline-block", lineHeight: 1.55 }}>{e.claim}</span>
    ),
  },
  { key: "type", header: "Type", render: (e: Evidence) => <Badge color="navySoft">{e.type}</Badge> },
  { key: "mlr", header: "MLR status", render: (e: Evidence) => <Badge color="neutral">{e.mlr_status}</Badge> },
  {
    key: "source",
    header: "Source",
    render: (e: Evidence) => e.publisher ?? (e.source_url ? new URL(e.source_url).hostname : "—"),
  },
  {
    key: "conf",
    header: "Confidence",
    render: (e: Evidence) => (
      <ConfidenceBadge source={e.source} origin={e.origin} as_of={e.as_of} confidence={e.confidence} />
    ),
  },
];

export function EvidenceLibrary() {
  const { brandId } = useParams();
  const { data: evidence, isLoading } = useEvidence(brandId);
  const { data: gaps } = useResearchGaps(brandId);
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const byType = useMemo(() => {
    if (!evidence?.length) return [];
    const counts = new Map<string, number>();
    for (const e of evidence) counts.set(e.type, (counts.get(e.type) ?? 0) + 1);
    return Array.from(counts.entries())
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [evidence]);

  const filtered = useMemo(
    () => (typeFilter === "all" ? evidence ?? [] : (evidence ?? []).filter((e) => e.type === typeFilter)),
    [evidence, typeFilter],
  );

  const highConfidence = evidence?.filter((e) => e.confidence >= 0.75).length ?? 0;
  const external = evidence?.filter((e) => e.origin === "external").length ?? 0;

  return (
    <div>
      <StageHeader stageId="evidence" />

      {!!evidence?.length && (
        <>
          <div className="grid grid-3" style={{ marginBottom: 22 }}>
            <Card style={{ margin: 0 }}>
              <MetricStat label="Claims captured" value={evidence.length} />
            </Card>
            <Card style={{ margin: 0 }}>
              <MetricStat label="High confidence" value={highConfidence} tone="emerald" sub="≥ 75%" />
            </Card>
            <Card style={{ margin: 0 }}>
              <MetricStat label="External sources" value={external} tone="gold" />
            </Card>
          </div>

          <ChartCard
            title="Evidence by type"
            subtitle={`${evidence.length} claims total`}
            height={Math.max(160, byType.length * 30)}
          >
            <BarChart data={byType} x="type" y="count" horizontal valueFormatter={(v) => v.toFixed(0)} />
          </ChartCard>

          <div style={{ height: 22 }} />
        </>
      )}

      <Card title={`Evidence (${filtered.length})`} sub="Filter by claim type, then review the source and confidence">
        {!!byType.length && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
            <Pill active={typeFilter === "all"} onClick={() => setTypeFilter("all")}>
              All ({evidence?.length ?? 0})
            </Pill>
            {byType.map((t) => (
              <Pill key={t.type} active={typeFilter === t.type} onClick={() => setTypeFilter(t.type)}>
                {t.type} ({t.count})
              </Pill>
            ))}
          </div>
        )}
        {isLoading ? (
          <SkeletonTable rows={6} cols={5} />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <DataTable
              rows={filtered}
              columns={columns}
              rowKey={(e) => e.id}
              emptyMessage="No evidence yet — run M1 (needs ANTHROPIC_API_KEY + SERPER_API_KEY)."
            />
          </div>
        )}
      </Card>

      <Card title={`Research gaps (${gaps?.length ?? 0})`} sub="Questions the research left unanswered or low-confidence">
        {gaps?.length ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
            {gaps.map((g) => (
              <AccentCallout key={g.id} tone="navy" label={g.block} icon={<HelpCircle size={12} />}>
                <div style={{ marginBottom: 8 }}>{g.question}</div>
                <Badge color="amber">{g.reason}</Badge>
              </AccentCallout>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<BookOpen size={24} strokeWidth={1.6} />}
            sub="No unanswered or low-confidence gaps recorded."
          />
        )}
      </Card>
    </div>
  );
}

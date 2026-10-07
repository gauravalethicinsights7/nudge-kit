import { useState } from "react";
import { useParams } from "react-router-dom";
import { Activity, FileText, Lightbulb, TrendingUp } from "lucide-react";
import { useMarketLandscape, useRunM1, useSystemStatus } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { EvidenceChip } from "../components/Badge";
import { ChartCard } from "../components/charts/ChartCard";
import { FunnelChart } from "../components/charts/FunnelChart";
import { SkeletonKpiRow } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  AccentCallout,
  Badge,
  BulletList,
  Card,
  ConfidencePill,
  EmptyState,
  Field,
  MetricStat,
  SectionHeading,
} from "../components/shared/ui";
import { normalizeBullets, toBullets } from "../lib/bullets";

export function MarketLandscape() {
  const { brandId } = useParams();
  const { data: landscape, isLoading } = useMarketLandscape(brandId);
  const { data: status } = useSystemStatus();
  const runM1 = useRunM1(brandId);
  const [openFact, setOpenFact] = useState<number | null>(null);
  const [paradigmOpen, setParadigmOpen] = useState(false);

  const disabledReason = !status?.anthropic_configured
    ? "ANTHROPIC_API_KEY is not configured"
    : !status?.serper_configured
    ? "SERPER_API_KEY is not configured — web research is unavailable"
    : null;

  const funnel = landscape?.patient_funnel;
  const funnelData = funnel
    ? [
        { name: "Prevalent", value: funnel.prevalent?.value ?? 0 },
        { name: "Diagnosed", value: funnel.diagnosed?.value ?? 0 },
        { name: "Treated", value: funnel.treated?.value ?? 0 },
        { name: "Controlled", value: funnel.controlled?.value ?? 0 },
      ].filter((d) => d.value > 0)
    : [];

  const unmetNeeds = normalizeBullets(landscape?.unmet_needs ?? []);
  const fact = openFact !== null ? landscape?.key_facts[openFact] : null;

  return (
    <div>
      <SectionHeading
        eyebrow="M1 · Understand the market"
        title="Market Landscape"
        sub="Patient funnel, market size and unmet needs — discovered by the research agent, every fact carrying evidence."
        right={
          <RunButton
            label="Run M1 (research)"
            onRun={() => runM1.mutate({})}
            isPending={runM1.isPending}
            disabledReason={disabledReason}
            error={runM1.error}
          />
        }
      />

      {isLoading && <SkeletonKpiRow count={2} />}
      {!isLoading && !landscape && (
        <Card>
          <EmptyState
            icon={<Activity size={28} strokeWidth={1.6} />}
            title="No market landscape yet"
            sub="Run the research agent once both API keys are configured — it searches, extracts evidence, and synthesizes the patient funnel, market size, and unmet needs."
          />
        </Card>
      )}

      {landscape && (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1.15fr) minmax(0, 1fr)",
              gap: 16,
              marginBottom: 22,
              alignItems: "stretch",
            }}
          >
            <ChartCard
              title="Patient funnel"
              subtitle="Prevalent → diagnosed → treated → controlled"
              height={280}
              isEmpty={!funnelData.length}
              emptyMessage="No funnel data extracted yet."
            >
              <FunnelChart data={funnelData} valueFormatter={(v) => v.toLocaleString()} />
            </ChartCard>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <Card style={{ margin: 0 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <MetricStat
                    label="Market size"
                    value={landscape.market_size ? landscape.market_size.value.toLocaleString() : "–"}
                    sub={landscape.market_size?.currency ?? undefined}
                  />
                  <MetricStat
                    label="Growth"
                    value={landscape.growth_pct ? `${landscape.growth_pct.value}%` : "–"}
                    sub={landscape.growth_pct ? "CAGR" : undefined}
                    tone="gold"
                  />
                </div>
                {landscape.market_size && (
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      flexWrap: "wrap",
                      marginTop: 14,
                      paddingTop: 12,
                      borderTop: "1px solid var(--border)",
                    }}
                  >
                    <Badge color="navySoft">{landscape.market_size.origin}</Badge>
                    <Badge color="neutral">As of {landscape.market_size.as_of}</Badge>
                    <ConfidencePill level={landscape.market_size.confidence} />
                  </div>
                )}
              </Card>

              <Card
                title="Paradigm"
                clickable={!!landscape.paradigm}
                onClick={() => setParadigmOpen(true)}
                style={{ margin: 0, flex: 1 }}
              >
                {landscape.paradigm ? (
                  <>
                    <BulletList items={toBullets(landscape.paradigm.text).slice(0, 3)} size={12.5} />
                    <div style={{ marginTop: 12 }}>
                      <EvidenceChip count={landscape.paradigm.evidence_ids.length} />
                    </div>
                  </>
                ) : (
                  <p style={{ fontSize: 13, color: "var(--text-3)" }}>Not available.</p>
                )}
              </Card>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
              gap: 16,
              alignItems: "start",
            }}
          >
            <Card
              title="Unmet needs"
              sub={`${unmetNeeds.length} gaps the brand can credibly address`}
              style={{ margin: 0 }}
            >
              {unmetNeeds.length ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {unmetNeeds.map((n, i) => (
                    <AccentCallout key={i} tone={i === 0 ? "gold" : "navy"}>
                      {n}
                    </AccentCallout>
                  ))}
                </div>
              ) : (
                <EmptyState icon={<Lightbulb size={24} strokeWidth={1.6} />} sub="None recorded." />
              )}
            </Card>

            <Card
              title="Key facts"
              sub={`${landscape.key_facts.length} evidenced claims — select one for sources`}
              style={{ margin: 0 }}
            >
              {landscape.key_facts.length ? (
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {landscape.key_facts.map((f, i) => (
                    <button
                      key={i}
                      onClick={() => setOpenFact(i)}
                      style={{
                        all: "unset",
                        cursor: "pointer",
                        display: "block",
                        padding: "12px 0",
                        borderBottom:
                          i === landscape.key_facts.length - 1 ? "none" : "1px solid var(--border)",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          gap: 10,
                          alignItems: "flex-start",
                        }}
                      >
                        <FileText
                          size={13}
                          strokeWidth={2}
                          style={{ color: "var(--gold-muted)", flexShrink: 0, marginTop: 3 }}
                        />
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>
                            {f.text}
                          </div>
                          <div style={{ marginTop: 6 }}>
                            <EvidenceChip count={f.evidence_ids.length} />
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <EmptyState icon={<TrendingUp size={24} strokeWidth={1.6} />} sub="None recorded." />
              )}
            </Card>
          </div>
        </>
      )}

      <DetailModal
        open={openFact !== null}
        onClose={() => setOpenFact(null)}
        eyebrow="Key fact"
        title="Evidenced claim"
      >
        {fact && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <Field label="Claim">{fact.text}</Field>
            <Field label="Evidence">
              <EvidenceChip count={fact.evidence_ids.length} />
              <BulletList
                items={fact.evidence_ids.map((id) => `Evidence ${id.slice(0, 8)} — see Evidence Library`)}
                size={12.5}
                style={{ marginTop: 10 }}
              />
            </Field>
          </div>
        )}
      </DetailModal>

      <DetailModal
        open={paradigmOpen}
        onClose={() => setParadigmOpen(false)}
        eyebrow="Treatment context"
        title="Paradigm"
        width={760}
      >
        {landscape?.paradigm && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <Field label="Where the brand sits today">
              <BulletList items={toBullets(landscape.paradigm.text)} />
            </Field>
            <Field label="Evidence">
              <EvidenceChip count={landscape.paradigm.evidence_ids.length} />
            </Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

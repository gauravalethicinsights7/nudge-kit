import { useState } from "react";
import { useParams } from "react-router-dom";
import { Activity, FileText, Lightbulb, TrendingDown } from "lucide-react";
import { useMarketLandscape, useRunM1, useSystemStatus } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { EvidenceChip } from "../components/Badge";
import { ChartCard } from "../components/charts/ChartCard";
import { FunnelChart } from "../components/charts/FunnelChart";
import { SkeletonKpiRow } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import { StageHeader } from "../components/shared/StageHeader";
import {
  Figure,
  HowCalculated,
  ProvenanceChip,
  gradeOf,
} from "../components/shared/provenance";
import {
  AccentCallout,
  BulletList,
  Card,
  EmptyState,
  Field,
} from "../components/shared/ui";
import { normalizeBullets, toBullets } from "../lib/bullets";
import type { ProvNumber } from "../api/types";

const fmt = (n: number) => n.toLocaleString(undefined, { maximumFractionDigits: 1 });

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
  const stages: { name: string; p: ProvNumber | null }[] = [
    { name: "Prevalent", p: funnel?.prevalent ?? null },
    { name: "Diagnosed", p: funnel?.diagnosed ?? null },
    { name: "Treated", p: funnel?.treated ?? null },
    { name: "Controlled", p: funnel?.controlled ?? null },
  ];
  const funnelData = stages
    .filter((s) => (s.p?.value ?? 0) > 0)
    .map((s) => ({ name: s.name, value: s.p!.value }));

  // The absolute numbers are the easy part; the drop between stages is where
  // the decision lives. Computed here rather than asserted, so each step can
  // be checked against the two figures it came from.
  const steps = stages
    .map((s, i) => ({ from: stages[i - 1], to: s }))
    .filter((x) => x.from?.p?.value && x.to.p?.value)
    .map((x) => {
      const pct = (x.to.p!.value / x.from!.p!.value) * 100;
      return {
        label: `${x.from!.name} → ${x.to.name}`,
        from: x.from!.p!,
        to: x.to.p!,
        pct,
        // A funnel stage cannot be larger than the one above it. When the two
        // extracted figures imply that, the units disagree (one source in
        // millions, another a percentage) — say so rather than printing a
        // 650% "conversion" as though it were a finding.
        inconsistent: pct > 100,
      };
    });
  const validSteps = steps.filter((s) => !s.inconsistent);
  const worstStep = validSteps.length
    ? validSteps.reduce((a, b) => (a.pct <= b.pct ? a : b))
    : null;
  const inconsistentSteps = steps.filter((s) => s.inconsistent);

  const unmetNeeds = normalizeBullets(landscape?.unmet_needs ?? []);
  const fact = openFact !== null ? landscape?.key_facts[openFact] : null;

  return (
    <div>
      <StageHeader
        stageId="m1"
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
            sub="Run the research agent once both API keys are configured. It searches, opens each source, extracts single facts, scores each one's confidence, and leaves a gap where nothing reached the bar rather than guessing."
          />
        </Card>
      )}

      {landscape && (
        <>
          {worstStep && (
            <AccentCallout tone="navy" label="Where the market leaks most" style={{ marginBottom: 18 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-1)", marginBottom: 4 }}>
                Only {worstStep.pct.toFixed(1)}% of{" "}
                {worstStep.label.split(" → ")[0].toLowerCase()} patients reach{" "}
                {worstStep.label.split(" → ")[1].toLowerCase()}.
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-3)" }}>
                The steepest drop in the funnel — the stage where effort returns the most patients.
              </div>
              <HowCalculated
                formula="Conversion = patients at this stage ÷ patients at the stage before, × 100."
                steps={[
                  { label: worstStep.label.split(" → ")[0], value: fmt(worstStep.from.value) },
                  { label: worstStep.label.split(" → ")[1], value: fmt(worstStep.to.value) },
                ]}
                result={`${worstStep.pct.toFixed(1)}%`}
                note="Both figures carry their own source and confidence — open the funnel card to see them."
              />
            </AccentCallout>
          )}

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
              {steps.length > 0 && (
                <div
                  style={{
                    marginTop: 14,
                    paddingTop: 12,
                    borderTop: "1px solid var(--border)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  {steps.map((s) => (
                    <div
                      key={s.label}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: 12,
                        fontSize: 12.5,
                      }}
                    >
                      <span style={{ color: "var(--text-2)" }}>{s.label}</span>
                      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <ProvenanceChip
                          grade={gradeOf(s.to.origin)}
                          prov={s.to}
                          compact
                        />
                        {s.inconsistent ? (
                          <span
                            title={`${s.from.value} then ${s.to.value} — a later stage cannot be larger. Sources: ${s.from.source} / ${s.to.source}`}
                            style={{
                              fontWeight: 700,
                              color: "var(--amber-text)",
                              minWidth: 46,
                              textAlign: "right",
                              cursor: "help",
                            }}
                          >
                            units ?
                          </span>
                        ) : (
                          <span
                            className="tabular"
                            style={{
                              fontWeight: 700,
                              color: s === worstStep ? "var(--red-text)" : "var(--navy)",
                              minWidth: 46,
                              textAlign: "right",
                            }}
                          >
                            {s.pct.toFixed(1)}%
                          </span>
                        )}
                      </span>
                    </div>
                  ))}
                  {inconsistentSteps.length > 0 && (
                    <div
                      style={{
                        marginTop: 4,
                        fontSize: 11.5,
                        lineHeight: 1.55,
                        color: "var(--amber-text)",
                        background: "var(--amber-bg)",
                        borderRadius: "var(--radius-sm)",
                        padding: "8px 10px",
                      }}
                    >
                      {inconsistentSteps.length === 1 ? "One step is" : `${inconsistentSteps.length} steps are`}{" "}
                      larger than the stage above, so the two sources are not on the same unit. Shown
                      as unresolved rather than converted — re-run M1 or correct the source figures.
                    </div>
                  )}
                </div>
              )}
            </ChartCard>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <Card style={{ margin: 0 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
                  <Figure
                    label="Market size"
                    value={landscape.market_size ? fmt(landscape.market_size.value) : "–"}
                    unit={landscape.market_size?.currency}
                    grade={landscape.market_size ? gradeOf(landscape.market_size.origin) : undefined}
                    prov={landscape.market_size ?? undefined}
                    sub={
                      landscape.market_size?.low != null && landscape.market_size?.high != null
                        ? `Sources disagree — range ${fmt(landscape.market_size.low)}–${fmt(landscape.market_size.high)}, kept as a range rather than averaged`
                        : landscape.market_size
                        ? `Source: ${landscape.market_size.source}`
                        : undefined
                    }
                  />
                  <Figure
                    label="Growth"
                    value={landscape.growth_pct ? `${landscape.growth_pct.value}%` : "–"}
                    unit={landscape.growth_pct ? "CAGR" : undefined}
                    tone="gold"
                    grade={landscape.growth_pct ? gradeOf(landscape.growth_pct.origin) : undefined}
                    prov={landscape.growth_pct ?? undefined}
                  />
                </div>
              </Card>

              <Card
                title="Paradigm"
                sub="Where the brand sits in today's treatment sequence"
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
                      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
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
                <EmptyState icon={<TrendingDown size={24} strokeWidth={1.6} />} sub="None recorded." />
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

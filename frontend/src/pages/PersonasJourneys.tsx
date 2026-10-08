import { useState } from "react";
import { useParams } from "react-router-dom";
import { Users } from "lucide-react";
import {
  useJourneyMaps, usePersonas, useRunM3CallNotes, useRunM3Social, useRunM3Survey, useRunM3Synthetic,
  useSystemStatus, useUploads,
} from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { StatusBadge } from "../components/Badge";
import { BarChart } from "../components/charts/BarChart";
import { SkeletonText } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  AvatarInitials,
  Badge,
  BulletList,
  Card,
  ConfidencePill,
  EmptyState,
  Field,
  MicroLabel,
  StepHeading,
} from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";
import { normalizeBullets } from "../lib/bullets";

export function PersonasJourneys() {
  const { brandId } = useParams();
  const { data: personas, isLoading } = usePersonas(brandId);
  const { data: journeyMaps } = useJourneyMaps(brandId);
  const { data: status } = useSystemStatus();
  const { data: uploads } = useUploads(brandId);
  const runSynthetic = useRunM3Synthetic(brandId);
  const runCallNotes = useRunM3CallNotes(brandId);
  const runSurvey = useRunM3Survey(brandId);
  const runSocial = useRunM3Social(brandId);
  const [personaCount, setPersonaCount] = useState(4);
  const [openPersona, setOpenPersona] = useState<string | null>(null);

  const disabledReason = !status?.anthropic_configured ? "ANTHROPIC_API_KEY is not configured" : null;
  const hasCallNotes = uploads?.some((u) => u.kind === "call_notes");
  const hasSurvey = uploads?.some((u) => u.kind === "survey_responses");
  const hasSocial = uploads?.some((u) => u.kind === "social_posts");

  const persona = personas?.find((p) => p.id === openPersona) ?? null;
  const journey = journeyMaps?.find((j) => j.persona_id === openPersona) ?? null;

  return (
    <div>
      <StageHeader
        stageId="m3"
                right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Count</label>
              <input type="number" min={1} max={8} value={personaCount} onChange={(e) => setPersonaCount(Number(e.target.value))} style={{ width: 70 }} />
            </div>
            <RunButton label="Run synthetic" onRun={() => runSynthetic.mutate({ persona_count: personaCount })} isPending={runSynthetic.isPending} disabledReason={disabledReason} error={runSynthetic.error} />
            <RunButton label="From call notes" onRun={() => runCallNotes.mutate({})} isPending={runCallNotes.isPending} disabledReason={disabledReason ?? (!hasCallNotes ? "No call-notes file uploaded" : null)} error={runCallNotes.error} primary={false} />
            <RunButton label="From survey" onRun={() => runSurvey.mutate({})} isPending={runSurvey.isPending} disabledReason={disabledReason ?? (!hasSurvey ? "No survey-responses file uploaded" : null)} error={runSurvey.error} primary={false} />
            <RunButton label="From social" onRun={() => runSocial.mutate({})} isPending={runSocial.isPending} disabledReason={disabledReason ?? (!hasSocial ? "No social-posts file uploaded" : null)} error={runSocial.error} primary={false} />
          </div>
        }
      />

      {isLoading && (
        <div className="grid grid-2">
          {[0, 1].map((i) => <Card key={i}><SkeletonText lines={4} /></Card>)}
        </div>
      )}

      {!isLoading && !personas?.length && (
        <Card>
          <EmptyState
            icon={<Users size={28} strokeWidth={1.6} />}
            title="No personas yet"
            sub="Run one of the derivation modes above. Synthetic needs only market context; the other three need a matching file uploaded in the Data Hub first."
          />
        </Card>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
        {personas?.map((p) => {
          const topChannels = Object.entries(p.channel_affinity)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 4)
            .map(([channel, affinity]) => ({ channel, affinity }));
          const barrierCount = Object.values(p.barriers_by_rung).reduce((n, b) => n + b.length, 0);

          return (
            <Card key={p.id} clickable onClick={() => setOpenPersona(p.id)} style={{ margin: 0 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: 14 }}>
                <AvatarInitials text={p.name} size={40} gold />
                <div style={{ minWidth: 0, flex: 1, paddingRight: 18 }}>
                  <div style={{ fontSize: 14.5, fontWeight: 700, color: "var(--text-1)", lineHeight: 1.3 }}>
                    {p.name}
                  </div>
                  <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                    <StatusBadge status={p.status} />
                    <Badge color="navySoft">{(p.share_of_universe * 100).toFixed(0)}% of universe</Badge>
                  </div>
                </div>
              </div>

              <MicroLabel>Top drivers</MicroLabel>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 14 }}>
                {p.drivers_ranked.slice(0, 3).map((d) => (
                  <Badge key={d} color="navy">{d}</Badge>
                ))}
              </div>

              {topChannels.length > 0 && (
                <>
                  <MicroLabel>Channel affinity</MicroLabel>
                  <BarChart
                    data={topChannels}
                    x="channel"
                    y="affinity"
                    horizontal
                    height={topChannels.length * 26 + 16}
                    valueFormatter={(v) => v.toFixed(2)}
                  />
                </>
              )}

              <div
                style={{
                  display: "flex",
                  gap: 14,
                  marginTop: 14,
                  paddingTop: 12,
                  borderTop: "1px solid var(--border)",
                  fontSize: 11.5,
                  color: "var(--text-3)",
                }}
              >
                <span>{barrierCount} barriers</span>
                <span>{p.derivation}</span>
                <span>{p.assumption ? "Assumption" : "Evidenced"}</span>
              </div>
            </Card>
          );
        })}
      </div>

      <DetailModal
        open={!!persona}
        onClose={() => setOpenPersona(null)}
        eyebrow={persona ? `${persona.derivation} · ${persona.assumption ? "assumption" : "evidenced"}` : undefined}
        title={persona?.name ?? ""}
        width={860}
        right={persona ? <ConfidencePill level={persona.confidence} /> : undefined}
      >
        {persona && (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div>
              <StepHeading n={1} title="Ranked drivers" />
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {persona.drivers_ranked.map((d, i) => (
                  <Badge key={d} color={i === 0 ? "gold" : "navySoft"}>
                    {i + 1}. {d}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <StepHeading n={2} title="Barriers by rung" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16 }}>
                {Object.entries(persona.barriers_by_rung).map(([rung, barriers]) => (
                  <div
                    key={rung}
                    style={{
                      borderLeft: "3px solid var(--navy)",
                      background: "var(--bg-raised)",
                      borderRadius: "var(--radius-sm)",
                      padding: "12px 14px",
                    }}
                  >
                    <MicroLabel>{rung}</MicroLabel>
                    <BulletList items={normalizeBullets(barriers)} size={12.5} />
                  </div>
                ))}
              </div>
            </div>

            {journey && (
              <div>
                <StepHeading n={3} title={`Journey (${journey.steps.length} steps)`} />
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {journey.steps.map((s, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: 12,
                        alignItems: "flex-start",
                        padding: "12px 14px",
                        background: "var(--bg-raised)",
                        borderRadius: "var(--radius-sm)",
                      }}
                    >
                      <div
                        style={{
                          width: 22,
                          height: 22,
                          borderRadius: 6,
                          background: "var(--gold)",
                          color: "var(--navy)",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 11,
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
                          <Badge color="neutral">{s.from_rung}</Badge>
                          <span style={{ color: "var(--text-3)" }}>→</span>
                          <Badge color="navySoft">{s.to_rung}</Badge>
                        </div>
                        <div style={{ fontSize: 13, color: "var(--text-2)", lineHeight: 1.6 }}>{s.job}</div>
                        <div style={{ fontSize: 12, color: "var(--text-3)", marginTop: 4 }}>
                          Barrier: {s.barrier}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Field label="Channel affinity">
              <BulletList
                items={Object.entries(persona.channel_affinity)
                  .sort((a, b) => b[1] - a[1])
                  .map(([c, v]) => `${c} — ${v.toFixed(2)}`)}
                size={12.5}
              />
            </Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

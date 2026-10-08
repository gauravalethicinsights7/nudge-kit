import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Route, Workflow } from "lucide-react";
import { useActions, useJourneyRules, usePersonas, useRunM7, useSegments, useUploads } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { DownloadButton } from "../components/DownloadButton";
import { SkeletonKpiRow, SkeletonText } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  AccentCallout,
  Badge,
  BulletList,
  Card,
  EmptyState,
  Field,
  MetricStat,
  TableWrap,
} from "../components/shared/ui";
import { StageHeader } from "../components/shared/StageHeader";
import type { ContentBrief } from "../api/types";

const PREVIEW_RULES = 12;

export function Orchestration() {
  const { brandId } = useParams();
  const { data: journeyRules, isLoading } = useJourneyRules(brandId);
  const { data: actions } = useActions(brandId);
  const { data: segments } = useSegments(brandId);
  const { data: personas } = usePersonas(brandId);
  const { data: uploads } = useUploads(brandId);
  const runM7 = useRunM7(brandId);
  const [repCount, setRepCount] = useState<number | "">(50);
  const [lastBriefs, setLastBriefs] = useState<ContentBrief[]>([]);
  const [openRule, setOpenRule] = useState<string | null>(null);

  // content_briefs only exist in the M7 job's result once it finishes
  // (they're not persisted anywhere — see agents/m7/agent.py's own note).
  useEffect(() => {
    if (runM7.job?.status === "done" && runM7.job.result) {
      setLastBriefs((runM7.job.result.content_briefs as ContentBrief[] | undefined) ?? []);
    }
  }, [runM7.job?.status, runM7.job?.id]);

  const hasContentLibrary = uploads?.some((u) => u.kind === "content_library");
  const disabledReason = !segments?.length || !personas?.length
    ? "No segments/personas — run M2 and M3 first"
    : !hasContentLibrary
    ? "No content library uploaded — upload one in the Data Hub"
    : null;

  const maxScore = actions?.length ? Math.max(...actions.map((a) => a.score)) : 1;
  const doneCount = actions?.filter((a) => a.action_status === "done").length ?? 0;
  const rule = journeyRules?.find((r) => r.id === openRule) ?? null;

  return (
    <div>
      <StageHeader
        stageId="m7"
                right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10 }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Rep count</label>
              <input type="number" value={repCount} onChange={(e) => setRepCount(e.target.value === "" ? "" : Number(e.target.value))} style={{ width: 80 }} />
            </div>
            <RunButton
              label="Run M7"
              onRun={() => runM7.mutate({ rep_count: repCount === "" ? null : repCount })}
              isPending={runM7.isPending}
              disabledReason={disabledReason}
              error={runM7.error}
            />
          </div>
        }
      />

      {isLoading ? (
        <SkeletonKpiRow count={3} />
      ) : (
        <div className="grid grid-3" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Journey rules" value={journeyRules?.length ?? 0} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Actions this run" value={actions?.length ?? 0} tone="gold" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat
              label="Completed"
              value={doneCount}
              sub={actions?.length ? `of ${actions.length}` : undefined}
              tone="emerald"
            />
          </Card>
        </div>
      )}

      <Card
        title={`Journey rules (${journeyRules?.length ?? 0})`}
        sub="Select a rule to see its full sequence, escalation and exit signal"
      >
        {isLoading ? (
          <SkeletonText lines={4} />
        ) : journeyRules?.length ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
              {journeyRules.slice(0, PREVIEW_RULES).map((r) => (
                <button
                  key={r.id}
                  onClick={() => setOpenRule(r.id)}
                  style={{
                    all: "unset",
                    cursor: "pointer",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: 14,
                    background: "var(--bg-surface)",
                  }}
                >
                  <div
                    style={{
                      fontSize: 10.5,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.07em",
                      color: "var(--text-3)",
                      marginBottom: 8,
                    }}
                  >
                    Segment {r.segment_id.slice(0, 8)} × Persona {r.persona_id.slice(0, 8)}
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {r.steps.slice(0, 4).map((s, i) => (
                      <Badge key={i} color={i === 0 ? "navy" : "navySoft"}>
                        {s.channel}
                      </Badge>
                    ))}
                    {r.steps.length > 4 && <Badge color="neutral">+{r.steps.length - 4}</Badge>}
                  </div>
                </button>
              ))}
            </div>
            {journeyRules.length > PREVIEW_RULES && (
              <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 14 }}>
                Showing the first {PREVIEW_RULES} of {journeyRules.length} journey rules.
              </p>
            )}
          </>
        ) : (
          <EmptyState icon={<Route size={24} strokeWidth={1.6} />} sub="No journey rules yet." />
        )}
      </Card>

      {lastBriefs.length > 0 && (
        <Card title="Content briefs from last run" sub="Gaps the content library could not fill">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 14 }}>
            {lastBriefs.map((b, i) => (
              <AccentCallout key={i} tone="gold" label={`${b.channel} · ${b.driver}`}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>{b.claim_needed}</div>
                <div style={{ fontSize: 12, color: "var(--text-3)" }}>{b.reason}</div>
              </AccentCallout>
            ))}
          </div>
        </Card>
      )}

      <Card
        title={`Actions (${actions?.length ?? 0})`}
        sub="Weekly next-best-action feed, scored and guardrail-checked"
        right={
          actions?.length ? (
            <>
              <DownloadButton path={`/brands/${brandId}/m7/actions/export.csv`} filename="actions.csv" label="Export CSV" />
              <DownloadButton path={`/brands/${brandId}/m7/actions/export.json`} filename="actions.json" label="Export JSON" />
            </>
          ) : undefined
        }
      >
        {actions?.length ? (
          <>
            <TableWrap minWidth={720}>
              <thead>
                <tr>
                  <th>HCP</th>
                  <th>Channel</th>
                  <th>Score</th>
                  <th>Reason</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {actions.slice(0, 50).map((a) => (
                  <tr key={a.id}>
                    <td>{a.hcp_id.slice(0, 8)}</td>
                    <td>
                      <Badge color="navySoft">{a.channel}</Badge>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{ width: `${(a.score / maxScore) * 100}%` }} />
                        </div>
                        <span className="tabular">{a.score.toFixed(2)}</span>
                      </div>
                    </td>
                    <td style={{ fontSize: 11.5, maxWidth: 360 }}>{a.reason}</td>
                    <td>
                      <Badge color={a.action_status === "done" ? "emerald" : "neutral"}>{a.action_status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
            {actions.length > 50 && (
              <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 12 }}>
                Showing the first 50 of {actions.length} — use the CSV or JSON export for the full feed.
              </p>
            )}
          </>
        ) : (
          <EmptyState icon={<Workflow size={24} strokeWidth={1.6} />} sub="No actions yet." />
        )}
      </Card>

      <DetailModal
        open={!!rule}
        onClose={() => setOpenRule(null)}
        eyebrow="Journey rule"
        title={rule ? `Segment ${rule.segment_id.slice(0, 8)} × Persona ${rule.persona_id.slice(0, 8)}` : ""}
        width={780}
      >
        {rule && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <Field label={`Sequence (${rule.steps.length} steps)`}>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {rule.steps.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      gap: 12,
                      alignItems: "center",
                      padding: "10px 14px",
                      background: "var(--bg-raised)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <div
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: 6,
                        background: "var(--navy)",
                        color: "var(--text-inv)",
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
                    <Badge color="navySoft">{s.channel}</Badge>
                    <span style={{ fontSize: 12.5, color: "var(--text-3)" }}>
                      Wait {s.wait_days}d · content{" "}
                      {s.content_ref ? s.content_ref.slice(0, 8) : "missing (see content brief)"}
                    </span>
                  </div>
                ))}
              </div>
            </Field>
            <Field label="Escalation">
              {rule.escalation.length ? (
                <BulletList items={rule.escalation.map((e) => `${e.signal} → ${e.action}`)} size={12.5} />
              ) : (
                "None defined."
              )}
            </Field>
            <Field label="Exit signal">{rule.exit_signal}</Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

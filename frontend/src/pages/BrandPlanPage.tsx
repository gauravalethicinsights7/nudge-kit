import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, FileCheck, ShieldCheck } from "lucide-react";
import { useBrandPlan, useRunM5, useSystemStatus } from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { DownloadButton } from "../components/DownloadButton";
import { ChartCard } from "../components/charts/ChartCard";
import { BarChart } from "../components/charts/BarChart";
import { SkeletonText } from "../components/Skeleton";
import { DetailModal } from "../components/shared/DetailModal";
import {
  AccentCallout,
  Badge,
  BulletList,
  Card,
  EmptyState,
  Field,
  MetricStat,
  SectionHeading,
  StepHeading,
  TableWrap,
} from "../components/shared/ui";
import { toBullets } from "../lib/bullets";

export function BrandPlanPage() {
  const { brandId } = useParams();
  const { data: plan, isLoading } = useBrandPlan(brandId);
  const { data: status } = useSystemStatus();
  const runM5 = useRunM5(brandId);

  const [netPrice, setNetPrice] = useState(5000);
  const [budgetEnvelope, setBudgetEnvelope] = useState<number | "">("");
  const [requireApproval, setRequireApproval] = useState(true);
  const [openIssue, setOpenIssue] = useState<string | null>(null);

  const disabledReason = !status?.anthropic_configured ? "ANTHROPIC_API_KEY is not configured" : null;

  const scenarioData = plan
    ? [
        { scenario: "Downside", delta_nrx: plan.forecast.downside.delta_nrx },
        { scenario: "Base", delta_nrx: plan.forecast.base.delta_nrx },
        { scenario: "Upside", delta_nrx: plan.forecast.upside.delta_nrx },
      ]
    : [];

  const budgetByChannel = useMemo(() => {
    if (!plan || plan.budget.placeholder || !plan.budget.lines.length) return [];
    const totals = new Map<string, number>();
    for (const l of plan.budget.lines) {
      const key = l.channel_id ?? l.imperative_id ?? "unassigned";
      totals.set(key, (totals.get(key) ?? 0) + l.amount.value);
    }
    return Array.from(totals.entries())
      .map(([channel, amount]) => ({ channel, amount }))
      .sort((a, b) => b.amount - a.amount);
  }, [plan]);

  const issue = plan?.key_issues.find((k) => k.id === openIssue) ?? null;
  const blockers = plan?.compliance_flags.filter((f) => f.severity === "block") ?? [];

  return (
    <div>
      <SectionHeading
        eyebrow="M5 · Decide the plan"
        title="Brand Plan"
        sub="Situation, key issues, imperatives, positioning, message house, objectives, forecast and budget — compliance-checked before export."
        right={
          <div style={{ display: "flex", alignItems: "flex-end", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Net price / month</label>
              <input type="number" value={netPrice} onChange={(e) => setNetPrice(Number(e.target.value))} style={{ width: 100 }} />
            </div>
            <div className="form-row" style={{ margin: 0 }}>
              <label>Budget envelope</label>
              <input
                type="number"
                placeholder="optional"
                value={budgetEnvelope}
                onChange={(e) => setBudgetEnvelope(e.target.value === "" ? "" : Number(e.target.value))}
                style={{ width: 110 }}
              />
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 6, textTransform: "none", letterSpacing: 0, fontSize: 12, fontWeight: 500, color: "var(--text-2)", marginBottom: 8 }}>
              <input type="checkbox" checked={requireApproval} onChange={(e) => setRequireApproval(e.target.checked)} />
              Require upstream approval
            </label>
            <RunButton
              label="Run M5"
              onRun={() =>
                runM5.mutate({
                  net_price: netPrice,
                  budget_envelope: budgetEnvelope === "" ? null : budgetEnvelope,
                  plan_horizon_months: 12,
                  require_approval: requireApproval,
                })
              }
              isPending={runM5.isPending}
              disabledReason={disabledReason}
              error={runM5.error}
            />
          </div>
        }
      />

      {isLoading && <Card><SkeletonText lines={4} /></Card>}
      {!isLoading && !plan && (
        <Card>
          <EmptyState
            icon={<FileCheck size={28} strokeWidth={1.6} />}
            title="No brand plan yet"
            sub="Requires segments and personas (and ideally market landscape plus competitive data) to already exist. Run M5 once they are ready."
          />
        </Card>
      )}

      {plan && (
        <>
          {blockers.length > 0 && (
            <AccentCallout
              tone="red"
              label="Compliance blockers"
              icon={<AlertTriangle size={12} />}
              style={{ marginBottom: 18 }}
            >
              <BulletList items={blockers.map((f) => f.item)} size={12.5} />
            </AccentCallout>
          )}

          <Card
            title="Export"
            sub="Board-ready plan, generated from the approved objects"
            right={
              <>
                <DownloadButton path={`/brands/${brandId}/m5/brand-plan/export.md`} filename="brand_plan.md" label="Markdown" />
                <DownloadButton path={`/brands/${brandId}/m5/brand-plan/export.docx`} filename="brand_plan.docx" label="DOCX" />
              </>
            }
          />

          <Card>
            <StepHeading n={1} title="Situation" />
            <BulletList items={toBullets(plan.situation.summary)} />
          </Card>

          <Card>
            <StepHeading
              n={2}
              title={`Key issues (${plan.key_issues.length})`}
              right={<Badge color="navySoft">Select one for detail</Badge>}
            />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
              {plan.key_issues.map((ki) => (
                <button
                  key={ki.id}
                  onClick={() => setOpenIssue(ki.id)}
                  style={{
                    all: "unset",
                    cursor: "pointer",
                    borderLeft: "3px solid var(--navy)",
                    background: "var(--bg-raised)",
                    borderRadius: "var(--radius-sm)",
                    padding: "14px 16px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-start",
                    gap: 10,
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-1)", lineHeight: 1.5 }}>
                    {toBullets(ki.statement)[0] ?? ki.statement}
                  </div>
                  <Badge color="gold">
                    {ki.revenue_at_stake.value.toLocaleString()} {ki.revenue_at_stake.currency} at stake
                  </Badge>
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <StepHeading n={3} title={`Imperatives (${plan.imperatives.length})`} />
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {plan.imperatives.map((i) => (
                <div
                  key={i.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 14,
                    padding: "10px 14px",
                    background: "var(--bg-raised)",
                    borderRadius: "var(--radius-sm)",
                  }}
                >
                  <span style={{ fontSize: 13, color: "var(--text-2)", fontWeight: 600 }}>{i.title}</span>
                  <Badge color="navySoft">
                    {i.from_rung} → {i.to_rung}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          <div className="grid grid-2">
            <Card>
              <StepHeading n={4} title="Positioning" />
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <Field label="Target">{plan.positioning.target}</Field>
                <Field label="Frame of reference">{plan.positioning.frame_of_reference}</Field>
                <Field label="Point of difference">
                  <div style={{ marginBottom: 8 }}>
                    <Badge color="gold">{plan.positioning.driver}</Badge>
                  </div>
                  {plan.positioning.point_of_difference}
                </Field>
              </div>
            </Card>

            <Card>
              <StepHeading n={5} title="Message house" />
              <AccentCallout tone="gold" label="Core message" style={{ marginBottom: 14 }}>
                {plan.message_house.core}
              </AccentCallout>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {plan.message_house.pillars.map((p, i) => (
                  <div key={i}>
                    <div
                      style={{
                        fontSize: 10.5,
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.07em",
                        color: "var(--text-3)",
                        marginBottom: 4,
                      }}
                    >
                      {p.driver}
                    </div>
                    <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{p.message}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card>
            <StepHeading n={6} title="Objectives" />
            {plan.objectives.length ? (
              <TableWrap minWidth={560}>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Baseline</th>
                    <th>Target</th>
                    <th>Due</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.objectives.map((o, i) => (
                    <tr key={i}>
                      <td>{o.metric}</td>
                      <td>{o.baseline}</td>
                      <td>{o.target}</td>
                      <td>{o.due}</td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            ) : (
              <EmptyState sub="No objectives set." />
            )}
          </Card>

          <Card>
            <StepHeading n={7} title="Forecast and budget" />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 16, marginBottom: 18 }}>
              <MetricStat
                label="Base revenue"
                value={plan.forecast.base.revenue.value.toLocaleString()}
                sub={plan.forecast.base.revenue.currency}
              />
              <MetricStat label="Base ROI" value={plan.forecast.base.roi?.toFixed(2) ?? "n/a"} tone="gold" />
              <MetricStat
                label="Budget lines"
                value={plan.budget.placeholder ? "—" : `${plan.budget.lines.length}`}
                sub={plan.budget.placeholder ? "Placeholder — run M6" : "Computed"}
              />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: budgetByChannel.length ? "1fr 1fr" : "1fr", gap: 16 }}>
              <ChartCard title="Forecast scenarios" subtitle="ΔNRx by scenario" height={200}>
                <BarChart data={scenarioData} x="scenario" y="delta_nrx" valueFormatter={(v) => v.toFixed(1)} height={200} />
              </ChartCard>
              {budgetByChannel.length > 0 && (
                <ChartCard title="Budget by channel" subtitle="Allocated spend" height={200}>
                  <BarChart
                    data={budgetByChannel}
                    x="channel"
                    y="amount"
                    horizontal
                    valueFormatter={(v) => v.toLocaleString()}
                    height={200}
                  />
                </ChartCard>
              )}
            </div>
          </Card>

          <Card>
            <StepHeading n={8} title="Compliance" right={<ShieldCheck size={15} style={{ color: "var(--emerald)" }} />} />
            {plan.compliance_flags.length ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {plan.compliance_flags.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <Badge color={f.severity === "block" ? "red" : "amber"}>{f.severity}</Badge>
                    <span style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{f.item}</span>
                  </div>
                ))}
              </div>
            ) : (
              <AccentCallout tone="emerald" label="Clear">
                No compliance flags raised against this plan.
              </AccentCallout>
            )}
          </Card>
        </>
      )}

      <DetailModal
        open={!!issue}
        onClose={() => setOpenIssue(null)}
        eyebrow="Key issue"
        title={issue ? `${issue.revenue_at_stake.value.toLocaleString()} ${issue.revenue_at_stake.currency} at stake` : ""}
        width={760}
      >
        {issue && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <Field label="Statement">
              <BulletList items={toBullets(issue.statement)} />
            </Field>
            <Field label="Barrier">
              <BulletList items={toBullets(issue.barrier)} />
            </Field>
          </div>
        )}
      </DetailModal>
    </div>
  );
}

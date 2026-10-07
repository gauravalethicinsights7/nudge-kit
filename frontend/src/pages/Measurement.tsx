import { useState } from "react";
import { useParams } from "react-router-dom";
import { FlaskConical, Gauge, SlidersHorizontal } from "lucide-react";
import {
  useAssumptionReviews, useLiftEstimates, usePriorUpdates, useRunAssumptionReview, useRunLiftTestDid,
  useRunLiftTestNational, useRunM8Outcomes, useRunPilotDesign, useRunPilotMatching, useRunPriorUpdate, useScorecard,
} from "../api/hooks";
import { RunButton } from "../components/RunButton";
import { RagPill } from "../components/Badge";
import { DownloadButton } from "../components/DownloadButton";
import { ApiError } from "../api/client";
import { ChartCard } from "../components/charts/ChartCard";
import { LiftBarChart } from "../components/charts/LiftBarChart";
import { SlopeChart } from "../components/charts/SlopeChart";
import { BulletBar } from "../components/charts/BulletBar";
import {
  AccentCallout,
  Badge,
  Card,
  EmptyState,
  MetricStat,
  SectionHeading,
  StepHeading,
  TableWrap,
} from "../components/shared/ui";

const RUNGS = ["unaware", "aware", "considering", "trialist", "adopter", "advocate", "lapsed"];

function parseNumbers(text: string): number[] {
  return text.split(",").map((s) => s.trim()).filter(Boolean).map(Number).filter((n) => !Number.isNaN(n));
}

export function Measurement() {
  const { brandId } = useParams();
  const { data: scorecard } = useScorecard(brandId);
  const { data: liftEstimates } = useLiftEstimates(brandId);
  const { data: priorUpdates } = usePriorUpdates(brandId);
  const { data: assumptionReviews } = useAssumptionReviews(brandId);

  const runOutcomes = useRunM8Outcomes(brandId);
  const runDid = useRunLiftTestDid(brandId);
  const runNational = useRunLiftTestNational(brandId);
  const runPriorUpdate = useRunPriorUpdate(brandId);
  const runAssumptionReview = useRunAssumptionReview(brandId);

  const [period, setPeriod] = useState("2026-01");
  const [testName, setTestName] = useState("Pilot test");
  const [testDeltas, setTestDeltas] = useState("5,6,4,5.5,6.2");
  const [controlDeltas, setControlDeltas] = useState("1,2,0.5,1.5,1.2");
  const [natName, setNatName] = useState("National launch");
  const [preValues, setPreValues] = useState("10,10.5,11,11.5,12,12.5");
  const [postValues, setPostValues] = useState("16,16.5,17,17.5");
  const [rung, setRung] = useState("aware");
  const [successes, setSuccesses] = useState(6);
  const [trials, setTrials] = useState(20);
  const [actualNrx, setActualNrx] = useState(95);
  const [effectSize, setEffectSize] = useState(2.0);
  const [std, setStd] = useState(5.0);
  const [power, setPower] = useState(0.8);
  const [alpha, setAlpha] = useState(0.05);
  const runPilotDesign = useRunPilotDesign(brandId);
  const runPilotMatching = useRunPilotMatching(brandId);

  const greens = scorecard?.kpis.filter((k) => k.rag === "green").length ?? 0;
  const reds = scorecard?.kpis.filter((k) => k.rag === "red").length ?? 0;

  return (
    <div>
      <SectionHeading
        eyebrow="M8 · Act and learn"
        title="Measurement"
        sub="Engagement index and scorecard versus plan, causal lift tests, prior recalibration and assumption review."
      />

      {scorecard && (
        <div className="grid grid-4" style={{ marginBottom: 22 }}>
          <Card style={{ margin: 0 }}>
            <MetricStat label="KPIs tracked" value={scorecard.kpis.length} />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="On plan" value={greens} tone="emerald" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Off plan" value={reds} tone="red" />
          </Card>
          <Card style={{ margin: 0 }}>
            <MetricStat label="Lift tests" value={liftEstimates?.length ?? 0} tone="gold" />
          </Card>
        </div>
      )}

      <Card
        title="Scorecard"
        sub="Actual versus plan for the selected period"
        right={
          scorecard ? (
            <>
              <DownloadButton path={`/brands/${brandId}/m8/scorecard/export.csv`} filename="scorecard.csv" label="CSV" />
              <DownloadButton path={`/brands/${brandId}/m8/scorecard/export.md`} filename="scorecard.md" label="Markdown" />
            </>
          ) : undefined
        }
      >
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, marginBottom: 16 }}>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Period (YYYY-MM)</label>
            <input value={period} onChange={(e) => setPeriod(e.target.value)} style={{ width: 110 }} />
          </div>
          <RunButton
            label="Run outcomes + scorecard"
            onRun={() => runOutcomes.mutate({ period })}
            isPending={runOutcomes.isPending}
            error={runOutcomes.error}
          />
        </div>
        {scorecard ? (
          <TableWrap minWidth={680}>
            <thead>
              <tr>
                <th>KPI</th>
                <th>Category</th>
                <th>Actual vs. plan</th>
                <th>Variance</th>
                <th>RAG</th>
              </tr>
            </thead>
            <tbody>
              {scorecard.kpis.map((k, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{k.name}</td>
                  <td>
                    <Badge color="navySoft">{k.category}</Badge>
                  </td>
                  <td>
                    <BulletBar actual={k.actual} plan={k.plan} rag={k.rag} />
                  </td>
                  <td>{k.variance?.toFixed(1) ?? "–"}</td>
                  <td>
                    <RagPill rag={k.rag} />
                  </td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        ) : (
          <EmptyState
            icon={<Gauge size={24} strokeWidth={1.6} />}
            sub="No scorecard yet — requires a brand plan (run M5 first)."
          />
        )}
      </Card>

      <div className="grid grid-2">
        <Card>
          <StepHeading n={1} title="Lift test — difference-in-differences" />
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Test name</label>
            <input value={testName} onChange={(e) => setTestName(e.target.value)} style={{ width: "100%" }} />
          </div>
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Test deltas (comma-separated)</label>
            <input value={testDeltas} onChange={(e) => setTestDeltas(e.target.value)} style={{ width: "100%" }} />
          </div>
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Control deltas</label>
            <input value={controlDeltas} onChange={(e) => setControlDeltas(e.target.value)} style={{ width: "100%" }} />
          </div>
          <RunButton
            label="Run DiD"
            onRun={() => runDid.mutate({ test_name: testName, test_deltas: parseNumbers(testDeltas), control_deltas: parseNumbers(controlDeltas) })}
            isPending={runDid.isPending}
            error={runDid.error}
          />
        </Card>
        <Card>
          <StepHeading n={2} title="Lift test — national counterfactual" />
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Test name</label>
            <input value={natName} onChange={(e) => setNatName(e.target.value)} style={{ width: "100%" }} />
          </div>
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Pre-period values</label>
            <input value={preValues} onChange={(e) => setPreValues(e.target.value)} style={{ width: "100%" }} />
          </div>
          <div className="form-row" style={{ maxWidth: "100%" }}>
            <label>Post-period values</label>
            <input value={postValues} onChange={(e) => setPostValues(e.target.value)} style={{ width: "100%" }} />
          </div>
          <RunButton
            label="Run counterfactual"
            onRun={() => runNational.mutate({ test_name: natName, pre_values: parseNumbers(preValues), post_values: parseNumbers(postValues) })}
            isPending={runNational.isPending}
            error={runNational.error}
          />
        </Card>
      </div>

      <div className="grid grid-2" style={{ alignItems: "start", marginBottom: 22 }}>
        <ChartCard
          title="Lift estimates"
          subtitle="Effect with 95% confidence interval"
          height={Math.max(160, (liftEstimates?.length ?? 0) * 50)}
          isEmpty={!liftEstimates?.length}
          emptyMessage="No lift tests run yet."
        >
          <LiftBarChart
            data={liftEstimates?.map((l) => ({ name: l.test_name, effect: l.effect, ci_low: l.ci_low, ci_high: l.ci_high })) ?? []}
            height={Math.max(160, (liftEstimates?.length ?? 0) * 50)}
          />
        </ChartCard>

        <Card title="Lift estimates — exact values" style={{ margin: 0 }}>
          {liftEstimates?.length ? (
            <TableWrap minWidth={420}>
              <thead>
                <tr>
                  <th>Test</th>
                  <th>Method</th>
                  <th>Effect</th>
                  <th>95% CI</th>
                </tr>
              </thead>
              <tbody>
                {liftEstimates.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontWeight: 600 }}>{l.test_name}</td>
                    <td>
                      <Badge color="navySoft">{l.method}</Badge>
                    </td>
                    <td>{l.effect.toFixed(2)}</td>
                    <td>
                      [{l.ci_low.toFixed(2)}, {l.ci_high.toFixed(2)}]
                    </td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          ) : (
            <EmptyState icon={<FlaskConical size={24} strokeWidth={1.6} />} sub="No lift tests run yet." />
          )}
        </Card>
      </div>

      <Card title="Prior updates" sub="Tenant-level and idempotent — never overwrites the market pack">
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Rung</label>
            <select value={rung} onChange={(e) => setRung(e.target.value)}>
              {RUNGS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Successes</label>
            <input type="number" value={successes} onChange={(e) => setSuccesses(Number(e.target.value))} style={{ width: 80 }} />
          </div>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Trials</label>
            <input type="number" value={trials} onChange={(e) => setTrials(Number(e.target.value))} style={{ width: 80 }} />
          </div>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Period</label>
            <input value={period} onChange={(e) => setPeriod(e.target.value)} style={{ width: 100 }} />
          </div>
          <RunButton
            label="Update prior"
            onRun={() => runPriorUpdate.mutate({ rung, successes, trials, period, pseudo_count: 10 })}
            isPending={runPriorUpdate.isPending}
            error={runPriorUpdate.error}
          />
        </div>
        {priorUpdates?.length ? (
          <>
            <SlopeChart
              data={priorUpdates.map((p) => ({ name: p.key, before: p.before, after: p.after }))}
              height={Math.max(140, priorUpdates.length * 36)}
              valueFormatter={(v) => v.toFixed(3)}
            />
            <div style={{ marginTop: 16 }}>
              <TableWrap minWidth={520}>
                <thead>
                  <tr>
                    <th>Rung</th>
                    <th>Period</th>
                    <th>Before</th>
                    <th>After</th>
                    <th>Version</th>
                  </tr>
                </thead>
                <tbody>
                  {priorUpdates.map((p) => (
                    <tr key={p.id}>
                      <td>{p.key}</td>
                      <td>{p.period}</td>
                      <td>{p.before.toFixed(3)}</td>
                      <td>{p.after.toFixed(3)}</td>
                      <td>{p.version}</td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </div>
          </>
        ) : (
          <EmptyState icon={<SlidersHorizontal size={24} strokeWidth={1.6} />} sub="No prior updates yet." />
        )}
      </Card>

      <Card title="Assumption review" sub="Did the plan's assumptions hold against actuals?">
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, marginBottom: 16 }}>
          <div className="form-row" style={{ margin: 0 }}>
            <label>Actual ΔNRx</label>
            <input type="number" value={actualNrx} onChange={(e) => setActualNrx(Number(e.target.value))} style={{ width: 90 }} />
          </div>
          <RunButton
            label="Run review"
            onRun={() => runAssumptionReview.mutate({ period, actual_values: { delta_nrx: actualNrx } })}
            isPending={runAssumptionReview.isPending}
            error={runAssumptionReview.error}
          />
        </div>
        {assumptionReviews?.length ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {assumptionReviews.map((r) => (
              <div key={r.id}>
                <div
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.07em",
                    color: "var(--text-3)",
                    marginBottom: 6,
                  }}
                >
                  {r.period}
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {r.items.map((it, i) => (
                    <Badge key={i} color={it.held ? "emerald" : "red"}>
                      {it.assumption}: {it.held ? "held" : "failed"} ({it.actual_value} vs {it.planned_value})
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState sub="No assumption reviews yet." />
        )}
      </Card>

      <Card title="Pilot design" sub="Size the test, then match comparable HCPs">
        <div className="grid grid-2">
          <div>
            <StepHeading n={1} title="Required sample size" />
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 14 }}>
              <div className="form-row" style={{ margin: 0 }}>
                <label>Effect size</label>
                <input type="number" step="0.1" value={effectSize} onChange={(e) => setEffectSize(Number(e.target.value))} style={{ width: 80 }} />
              </div>
              <div className="form-row" style={{ margin: 0 }}>
                <label>Std dev</label>
                <input type="number" step="0.1" value={std} onChange={(e) => setStd(Number(e.target.value))} style={{ width: 80 }} />
              </div>
              <div className="form-row" style={{ margin: 0 }}>
                <label>Power</label>
                <input type="number" step="0.05" value={power} onChange={(e) => setPower(Number(e.target.value))} style={{ width: 70 }} />
              </div>
              <div className="form-row" style={{ margin: 0 }}>
                <label>Alpha</label>
                <input type="number" step="0.01" value={alpha} onChange={(e) => setAlpha(Number(e.target.value))} style={{ width: 70 }} />
              </div>
              <button className="btn-navy" onClick={() => runPilotDesign.mutate({ effect_size: effectSize, std, power, alpha })} disabled={runPilotDesign.isPending}>
                {runPilotDesign.isPending ? "Computing…" : "Compute"}
              </button>
            </div>
            {runPilotDesign.data && (
              <AccentCallout tone="navy" label="Result">
                <MetricStat label="Per arm" value={runPilotDesign.data.required_sample_size_per_arm} sub="HCPs required" />
              </AccentCallout>
            )}
            {runPilotDesign.error && (
              <p style={{ fontSize: 12, color: "var(--red-text)" }}>
                {runPilotDesign.error instanceof ApiError ? runPilotDesign.error.detail : String(runPilotDesign.error)}
              </p>
            )}
          </div>
          <div>
            <StepHeading n={2} title="Matched pairs" />
            <button className="btn-ghost" onClick={() => runPilotMatching.mutate()} disabled={runPilotMatching.isPending} style={{ marginBottom: 14 }}>
              {runPilotMatching.isPending ? "Matching…" : "Suggest matched pairs"}
            </button>
            {runPilotMatching.error && (
              <p style={{ fontSize: 12, color: "var(--red-text)" }}>
                {runPilotMatching.error instanceof ApiError ? runPilotMatching.error.detail : String(runPilotMatching.error)}
              </p>
            )}
            {runPilotMatching.data &&
              (runPilotMatching.data.length ? (
                <TableWrap minWidth={360}>
                  <thead>
                    <tr>
                      <th>HCP A</th>
                      <th>HCP B</th>
                      <th>Distance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runPilotMatching.data.slice(0, 10).map((p, i) => (
                      <tr key={i}>
                        <td>{p.hcp_a}</td>
                        <td>{p.hcp_b}</td>
                        <td>{p.distance.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </TableWrap>
              ) : (
                <EmptyState sub="No pairs — needs at least two HCPs uploaded." />
              ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

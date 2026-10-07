// Actual-vs-plan bullet bar (spec §13/§16 "bullet chart: actual vs target").
// Plain CSS rather than a full chart — a single bar + target tick doesn't
// need ECharts overhead, and it reads correctly inline inside a table row.
export function BulletBar({
  actual,
  plan,
  rag,
}: {
  actual: number;
  plan: number | null;
  rag: "green" | "amber" | "red" | null;
}) {
  const ragColor = rag === "red" ? "var(--color-red)" : rag === "amber" ? "var(--color-amber)" : "var(--color-green)";
  const scale = Math.max(actual, plan ?? 0, 1) * 1.2;
  const actualPct = Math.min(100, (actual / scale) * 100);
  const planPct = plan !== null ? Math.min(100, (plan / scale) * 100) : null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ position: "relative", width: 110, height: 8, background: "var(--color-surface-muted)", borderRadius: 4 }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${actualPct}%`, background: ragColor, borderRadius: 4 }} />
        {planPct !== null && (
          <div
            title={`Plan: ${plan}`}
            style={{ position: "absolute", left: `${planPct}%`, top: -2, bottom: -2, width: 2, background: "var(--color-text)" }}
          />
        )}
      </div>
    </div>
  );
}

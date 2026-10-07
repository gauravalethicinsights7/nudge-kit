import type { ReactNode } from "react";

// Answers "what changed," not just "what is the number" (spec §13).
export function KPICard({
  label,
  value,
  delta,
  deltaDirection,
  comparisonLabel,
  driver,
  meta,
  right,
}: {
  label: string;
  value: ReactNode;
  delta?: string;
  deltaDirection?: "up" | "down" | "flat";
  comparisonLabel?: string;
  driver?: string;
  meta?: string;
  right?: ReactNode;
}) {
  return (
    <div className="kpi-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div className="kpi-label">{label}</div>
        {right}
      </div>
      <div className="kpi-value-row">
        <span className="kpi-value tabular">{value}</span>
        {delta && (
          <span className={`kpi-delta ${deltaDirection ?? "flat"}`}>
            {deltaDirection === "up" ? "↑" : deltaDirection === "down" ? "↓" : "→"} {delta}
          </span>
        )}
      </div>
      {comparisonLabel && <div className="kpi-meta">{comparisonLabel}</div>}
      {meta && !comparisonLabel && <div className="kpi-meta">{meta}</div>}
      {driver && <div className="kpi-driver">{driver}</div>}
    </div>
  );
}

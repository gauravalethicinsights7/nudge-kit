import type { ReactNode } from "react";

// Spec §22 structure: headline -> key drivers -> confidence -> evidence/
// action links. Built from real computed values (deltas, rankings,
// comparisons already in the data), never invented copy — kept visually
// distinct from the LLM-backed Ask NUDGE panel, which is the only place
// actual AI-generated text appears.
export function InsightCard({
  kicker = "Signal",
  headline,
  drivers,
  confidence,
  footer,
}: {
  kicker?: string;
  headline: ReactNode;
  drivers?: string[];
  confidence?: "High" | "Medium" | "Low";
  footer?: ReactNode;
}) {
  return (
    <div className="insight-card">
      <div className="insight-kicker">
        <span>&#9679;</span> {kicker}
      </div>
      <div className="insight-headline">{headline}</div>
      {drivers && drivers.length > 0 && (
        <ul className="insight-drivers">
          {drivers.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      )}
      {(confidence || footer) && (
        <div className="insight-footer">
          {confidence && (
            <span style={{ fontSize: 11.5, color: "var(--color-text-muted)" }}>
              Confidence: <strong style={{ color: "var(--color-text)" }}>{confidence}</strong>
            </span>
          )}
          {footer}
        </div>
      )}
    </div>
  );
}

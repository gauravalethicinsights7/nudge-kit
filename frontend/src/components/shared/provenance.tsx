import type { CSSProperties, ReactNode } from "react";
import { useState } from "react";
import { Calculator, CircleHelp, Database, FlaskConical } from "lucide-react";
import type { Origin, Prov } from "../../api/types";

/* The trust layer.
 *
 * Two rules the engine holds everywhere, made visible:
 *   1. The model writes and explains; it never does the arithmetic. Every
 *      number comes from a fixed formula that can be checked — <HowCalculated>.
 *   2. Every number says whether it is measured, estimated or an assumption —
 *      <ProvenanceChip>, derived from the real `origin` / `assumption` fields
 *      rather than decided in the view.
 */

export type Grade = "measured" | "estimated" | "assumption";

/** origin=external|internal means it came from real data; estimated means a
 *  proxy. An explicit assumption flag outranks both. */
export function gradeOf(origin: Origin | undefined, assumption?: boolean): Grade {
  if (assumption) return "assumption";
  if (origin === "estimated") return "estimated";
  return "measured";
}

const GRADE_META: Record<Grade, { label: string; bg: string; fg: string; blurb: string }> = {
  measured: {
    label: "Measured",
    bg: "var(--emerald-bg)",
    fg: "var(--emerald-text)",
    blurb: "From real data — a source you can open.",
  },
  estimated: {
    label: "Estimated",
    bg: "var(--amber-bg)",
    fg: "var(--amber-text)",
    blurb: "Derived from proxies, not observed directly.",
  },
  assumption: {
    label: "Assumption",
    bg: "var(--bg-raised)",
    fg: "var(--text-3)",
    blurb: "A stated guess. Change it and the numbers move.",
  },
};

export function ProvenanceChip({
  grade,
  prov,
  compact,
}: {
  grade: Grade;
  prov?: Partial<Prov>;
  compact?: boolean;
}) {
  const m = GRADE_META[grade];
  const title = [
    m.blurb,
    prov?.source ? `source: ${prov.source}` : null,
    prov?.as_of ? `as of: ${prov.as_of}` : null,
    prov?.confidence != null ? `confidence: ${(prov.confidence * 100).toFixed(0)}%` : null,
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <span
      title={title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: m.bg,
        color: m.fg,
        borderRadius: "var(--radius-pill)",
        padding: compact ? "0 7px" : "2px 9px",
        fontSize: compact ? 10 : 10.5,
        fontWeight: 700,
        letterSpacing: "0.02em",
        whiteSpace: "nowrap",
        cursor: "help",
      }}
    >
      {grade === "measured" ? (
        <Database size={9} strokeWidth={2.6} />
      ) : grade === "estimated" ? (
        <FlaskConical size={9} strokeWidth={2.6} />
      ) : (
        <CircleHelp size={9} strokeWidth={2.6} />
      )}
      {compact ? m.label[0] : m.label}
    </span>
  );
}

/** Thin confidence bar — reads faster than a percentage in a dense table. */
export function ConfidenceBar({ value, width = 38 }: { value: number; width?: number }) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  const tone = pct >= 75 ? "var(--emerald)" : pct >= 50 ? "var(--amber)" : "var(--red)";
  return (
    <span
      title={`confidence ${pct}%`}
      style={{ display: "inline-flex", alignItems: "center", gap: 6, whiteSpace: "nowrap" }}
    >
      <span
        style={{
          width,
          height: 5,
          borderRadius: 3,
          background: "var(--bg-raised)",
          border: "1px solid var(--border)",
          overflow: "hidden",
          display: "inline-block",
        }}
      >
        <span style={{ display: "block", width: `${pct}%`, height: "100%", background: tone }} />
      </span>
      <span className="tabular" style={{ fontSize: 11, color: "var(--text-3)" }}>
        {pct}%
      </span>
    </span>
  );
}

/* ---------------- How this is calculated ---------------- */

export interface CalcStep {
  label: string;
  value: ReactNode;
}

/** Formula in plain words, then the same formula with the numbers actually on
 *  screen substituted in. Collapsed by default — summaries first, the audit
 *  trail one click away. */
export function HowCalculated({
  formula,
  steps,
  result,
  note,
  label = "How this is calculated",
}: {
  formula: string;
  steps?: CalcStep[];
  result?: ReactNode;
  note?: string;
  label?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginTop: 10 }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          all: "unset",
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          fontSize: 11.5,
          fontWeight: 700,
          color: "var(--navy)",
        }}
      >
        <Calculator size={12} strokeWidth={2.4} />
        {open ? "Hide" : label}
      </button>

      {open && (
        <div
          style={{
            marginTop: 10,
            borderLeft: "3px solid var(--gold)",
            background: "var(--gold-light)",
            borderRadius: "var(--radius-sm)",
            padding: "12px 14px",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.07em",
                color: "var(--gold-muted)",
                marginBottom: 4,
              }}
            >
              Formula
            </div>
            <div style={{ fontSize: 12.5, lineHeight: 1.6, color: "var(--text-2)" }}>{formula}</div>
          </div>

          {!!steps?.length && (
            <div>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  color: "var(--gold-muted)",
                  marginBottom: 6,
                }}
              >
                With this brand's numbers
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {steps.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 14,
                      fontSize: 12.5,
                      color: "var(--text-2)",
                    }}
                  >
                    <span>{s.label}</span>
                    <span className="tabular" style={{ fontWeight: 600 }}>
                      {s.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result != null && (
            <div
              style={{
                borderTop: "1px solid var(--gold-pale)",
                paddingTop: 8,
                display: "flex",
                justifyContent: "space-between",
                gap: 14,
                fontSize: 13,
                fontWeight: 700,
                color: "var(--text-1)",
              }}
            >
              <span>Result</span>
              <span className="tabular">{result}</span>
            </div>
          )}

          {note && (
            <div style={{ fontSize: 11.5, color: "var(--text-3)", lineHeight: 1.55 }}>{note}</div>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------------- Figure ---------------- */

/** A headline number that answers all three questions at a glance: what it is,
 *  whether it can be trusted, and where it came from. */
export function Figure({
  label,
  value,
  unit,
  grade,
  prov,
  sub,
  tone,
  calc,
  style,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  grade?: Grade;
  prov?: Partial<Prov>;
  sub?: ReactNode;
  tone?: "navy" | "gold" | "emerald" | "red";
  calc?: ReactNode;
  style?: CSSProperties;
}) {
  const color =
    tone === "gold"
      ? "var(--gold-muted)"
      : tone === "emerald"
      ? "var(--emerald-text)"
      : tone === "red"
      ? "var(--red-text)"
      : "var(--navy)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5, minWidth: 0, ...style }}>
      <div
        style={{
          fontSize: 10.5,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          color: "var(--text-3)",
        }}
      >
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 7, flexWrap: "wrap" }}>
        <span
          className="tabular"
          style={{ fontSize: 26, fontWeight: 700, lineHeight: 1.1, color, letterSpacing: "-0.01em" }}
        >
          {value}
        </span>
        {unit && <span style={{ fontSize: 12.5, color: "var(--text-3)", fontWeight: 600 }}>{unit}</span>}
      </div>
      {(grade || prov?.confidence != null) && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          {grade && <ProvenanceChip grade={grade} prov={prov} />}
          {prov?.confidence != null && <ConfidenceBar value={prov.confidence} />}
        </div>
      )}
      {sub && <div style={{ fontSize: 11.5, color: "var(--text-3)", lineHeight: 1.5 }}>{sub}</div>}
      {calc}
    </div>
  );
}

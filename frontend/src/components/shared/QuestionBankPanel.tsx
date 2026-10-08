import { useState } from "react";
import { CheckCircle2, CircleSlash, MinusCircle } from "lucide-react";
import type { QuestionBankCoverage, QuestionCoverage } from "../../api/types";
import { Card, MicroLabel } from "./ui";
import { ConfidenceBar } from "./provenance";

/* Coverage of the fixed question bank.
 *
 * Every brand is researched against the same list, which is what turns "we
 * did thorough research" from a claim into something you can check. The
 * value here is not the answered count — it is seeing *which* block is thin,
 * because each block feeds a specific later module. A hollow channel block
 * means the channel plan is standing on nothing.
 */

/** Which module each question block feeds. Lets a gap be reported as a
 *  consequence ("the channel plan rests on this") instead of a statistic. */
const BLOCK_FEEDS: Record<string, string> = {
  disease_patient_flow: "the patient funnel and the size of the prize",
  treatment_paradigm: "positioning and the message house",
  market_access: "the forecast and pricing assumptions",
  prescriber_universe: "segments, eligibility and target lists",
  channel_landscape: "the channel mix and budget split",
  competitive_set: "the claim grid and open space",
  regulatory_compliance: "the guardrails on every action",
};

const STATUS_META = {
  answered: { label: "Answered", color: "var(--emerald-text)", bg: "var(--emerald-bg)", Icon: CheckCircle2 },
  partial: { label: "Low confidence", color: "var(--amber-text)", bg: "var(--amber-bg)", Icon: MinusCircle },
  gap: { label: "Gap", color: "var(--red-text)", bg: "var(--red-bg)", Icon: CircleSlash },
} as const;

function prettyBlock(block: string) {
  return block.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

function StatusPill({ q }: { q: QuestionCoverage }) {
  const m = STATUS_META[q.status];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: m.bg,
        color: m.color,
        borderRadius: "var(--radius-pill)",
        padding: "1px 8px",
        fontSize: 10.5,
        fontWeight: 700,
        whiteSpace: "nowrap",
      }}
    >
      <m.Icon size={9} strokeWidth={2.8} />
      {m.label}
    </span>
  );
}

export function QuestionBankPanel({ data }: { data: QuestionBankCoverage }) {
  const [open, setOpen] = useState<string | null>(null);

  if (!data.has_run) {
    return (
      <Card title="Question bank" sub={`${data.total} questions across ${data.blocks.length} blocks`}>
        <p style={{ fontSize: 13, color: "var(--text-3)", lineHeight: 1.6 }}>
          Not researched yet. Every brand is worked through the same fixed question bank, so no
          brand gets a shallower plan than another. Run M1 to see which questions the evidence
          actually answers.
        </p>
      </Card>
    );
  }

  const pct = Math.round((data.answered / Math.max(data.total, 1)) * 100);
  // A block with no answered questions is the one worth acting on: whatever
  // it feeds downstream has nothing underneath it.
  const hollow = data.blocks.filter((b) => b.questions.every((q) => q.status !== "answered"));

  return (
    <Card
      title="Question bank coverage"
      sub={`The same ${data.total} questions are asked of every brand — so "thorough" is checkable, not asserted`}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap", marginBottom: 10 }}>
        <span className="tabular" style={{ fontSize: 26, fontWeight: 700, color: "var(--navy)" }}>
          {data.answered}
          <span style={{ fontSize: 15, color: "var(--text-3)", fontWeight: 600 }}>/{data.total}</span>
        </span>
        <span style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <span style={{ fontSize: 12, color: "var(--emerald-text)", fontWeight: 700 }}>
            {data.answered} answered
          </span>
          {data.partial > 0 && (
            <span style={{ fontSize: 12, color: "var(--amber-text)", fontWeight: 700 }}>
              {data.partial} low confidence
            </span>
          )}
          {data.gap > 0 && (
            <span style={{ fontSize: 12, color: "var(--red-text)", fontWeight: 700 }}>
              {data.gap} gaps
            </span>
          )}
        </span>
      </div>

      <div
        style={{
          display: "flex",
          height: 8,
          borderRadius: 999,
          overflow: "hidden",
          background: "var(--bg-raised)",
          marginBottom: 14,
        }}
      >
        <span style={{ width: `${(data.answered / data.total) * 100}%`, background: "var(--emerald)" }} />
        <span style={{ width: `${(data.partial / data.total) * 100}%`, background: "var(--amber)" }} />
        <span style={{ width: `${(data.gap / data.total) * 100}%`, background: "var(--red)" }} />
      </div>

      {hollow.length > 0 && (
        <div
          style={{
            borderLeft: "3px solid var(--red)",
            background: "var(--red-bg)",
            borderRadius: "var(--radius-sm)",
            padding: "10px 14px",
            marginBottom: 14,
            fontSize: 12.5,
            lineHeight: 1.6,
            color: "var(--text-2)",
          }}
        >
          <strong style={{ color: "var(--red-text)" }}>
            {hollow.map((b) => prettyBlock(b.block)).join(" and ")} returned nothing.
          </strong>{" "}
          That block feeds {hollow.map((b) => BLOCK_FEEDS[b.block] ?? "later modules").join(" and ")}
          , so those are running on pack defaults rather than researched evidence.
        </div>
      )}

      <MicroLabel>By block — {pct}% answered overall</MicroLabel>
      <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 8 }}>
        {data.blocks.map((b) => {
          const answered = b.questions.filter((q) => q.status === "answered").length;
          const isOpen = open === b.block;
          const allAnswered = answered === b.questions.length;
          return (
            <div key={b.block}>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : b.block)}
                style={{
                  all: "unset",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  width: "100%",
                  padding: "9px 10px",
                  borderRadius: "var(--radius-sm)",
                  background: isOpen ? "var(--bg-raised)" : "transparent",
                }}
              >
                <span style={{ flex: 1, minWidth: 0, fontSize: 13, fontWeight: 600, color: "var(--text-1)" }}>
                  {prettyBlock(b.block)}
                </span>
                <span style={{ display: "flex", gap: 2, flexShrink: 0 }}>
                  {b.questions.map((q, i) => (
                    <span
                      key={i}
                      title={`${q.question} — ${STATUS_META[q.status].label}`}
                      style={{
                        width: 14,
                        height: 6,
                        borderRadius: 2,
                        background:
                          q.status === "answered"
                            ? "var(--emerald)"
                            : q.status === "partial"
                            ? "var(--amber)"
                            : "var(--red)",
                      }}
                    />
                  ))}
                </span>
                <span
                  className="tabular"
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: allAnswered ? "var(--emerald-text)" : "var(--text-3)",
                    minWidth: 34,
                    textAlign: "right",
                  }}
                >
                  {answered}/{b.questions.length}
                </span>
              </button>

              {isOpen && (
                <div
                  style={{
                    padding: "6px 10px 12px 10px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  <div style={{ fontSize: 11.5, color: "var(--text-3)", fontStyle: "italic" }}>
                    Feeds {BLOCK_FEEDS[b.block] ?? "later modules"}.
                  </div>
                  {b.questions.map((q, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: 10,
                        alignItems: "flex-start",
                        justifyContent: "space-between",
                      }}
                    >
                      <span style={{ fontSize: 12.5, lineHeight: 1.55, color: "var(--text-2)", flex: 1 }}>
                        {q.question}
                      </span>
                      <span style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                        {q.best_confidence != null && q.status === "partial" && (
                          <ConfidenceBar value={q.best_confidence} />
                        )}
                        <StatusPill q={q} />
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: 11.5, color: "var(--text-3)", lineHeight: 1.6, marginTop: 14 }}>
        A question counts as answered only when the supporting evidence reaches{" "}
        {(data.threshold * 100).toFixed(0)}% confidence. Below that it is reported as low
        confidence; with no evidence at all it stays a gap. Nothing is filled with a guess.
      </div>
    </Card>
  );
}

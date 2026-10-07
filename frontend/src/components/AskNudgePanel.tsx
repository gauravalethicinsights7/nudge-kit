import { useState } from "react";
import { useParams } from "react-router-dom";
import { MessageSquare, Send, Sparkles, X } from "lucide-react";
import { useAskNudge, useSystemStatus } from "../api/hooks";
import { ApiError } from "../api/client";
import { Badge, BulletList } from "./shared/ui";
import { toBullets } from "../lib/bullets";

export function AskNudgePanel() {
  const { brandId } = useParams<{ brandId?: string }>();
  const { data: status } = useSystemStatus();
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ question: string; answer: string }[]>([]);
  const ask = useAskNudge(brandId);

  if (!brandId) return null;

  const disabledReason = !status?.anthropic_configured ? "ANTHROPIC_API_KEY is not configured" : null;

  const onAsk = () => {
    if (!question.trim()) return;
    ask.mutate(question, {
      onSuccess: (resp) => {
        setHistory((h) => [...h, { question, answer: resp.answer }]);
        setQuestion("");
      },
    });
  };

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          position: "fixed",
          bottom: 22,
          right: 22,
          borderRadius: 999,
          width: 52,
          height: 52,
          zIndex: 30,
          boxShadow: "var(--shadow-md)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 0,
        }}
        className="btn-gold"
        title="Ask NUDGE"
      >
        {open ? <X size={19} /> : <MessageSquare size={19} />}
      </button>

      {open && (
        <div
          style={{
            position: "fixed",
            bottom: 86,
            right: 22,
            width: 380,
            maxHeight: 500,
            zIndex: 30,
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderTop: "3px solid var(--gold)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "var(--shadow-lg)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "14px 18px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 8,
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Sparkles size={15} style={{ color: "var(--gold-muted)" }} />
              <span
                className="wordmark"
                style={{ fontSize: 15 }}
              >
                Ask NUDGE
              </span>
            </span>
            <Badge color="gold">AI-generated</Badge>
          </div>

          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: 18,
              fontSize: 12.5,
              display: "flex",
              flexDirection: "column",
              gap: 18,
            }}
          >
            {history.length === 0 && (
              <BulletList
                items={[
                  "Ask about this brand's computed data — segments, personas, the plan or the scorecard.",
                  "Answers are grounded only in what the engine has actually produced for this brand.",
                ]}
                size={12.5}
              />
            )}
            {history.map((h, i) => (
              <div key={i}>
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
                  You asked
                </div>
                <div style={{ fontWeight: 600, marginBottom: 10, color: "var(--text-1)", lineHeight: 1.5 }}>
                  {h.question}
                </div>
                <BulletList items={toBullets(h.answer)} size={12.5} />
              </div>
            ))}
            {ask.isPending && <p style={{ color: "var(--text-3)", fontStyle: "italic" }}>Thinking…</p>}
          </div>

          <div style={{ padding: 14, borderTop: "1px solid var(--border)", background: "var(--bg-raised)" }}>
            {disabledReason ? (
              <p style={{ fontSize: 11.5, color: "var(--text-3)", margin: 0 }}>{disabledReason}</p>
            ) : (
              <>
                <div style={{ display: "flex", gap: 6 }}>
                  <input
                    style={{ flex: 1 }}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && onAsk()}
                    placeholder="Ask a question…"
                  />
                  <button className="btn-small btn-navy" onClick={onAsk} disabled={ask.isPending}>
                    <Send size={13} />
                  </button>
                </div>
                {ask.error && (
                  <p style={{ fontSize: 11, color: "var(--red-text)", marginTop: 6, marginBottom: 0 }}>
                    {ask.error instanceof ApiError ? ask.error.detail : String(ask.error)}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}

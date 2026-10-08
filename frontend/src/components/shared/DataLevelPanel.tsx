import { Check, Lock } from "lucide-react";
import type { UploadInfo } from "../../api/types";
import { Card, MicroLabel } from "./ui";

/* What the connected data actually unlocks.
 *
 * The engine can produce a credible first plan from public research alone,
 * but named doctor lists, fitted channel curves and measured return need the
 * client's own data. Saying so plainly is both honest and the clearest
 * argument for connecting the next source — the page sells the upgrade by
 * naming what is still estimated without it.
 */

interface Level {
  n: number;
  name: string;
  needs: string[];
  needsLabel: string;
  unlocks: string[];
  confidence: string;
}

const LEVELS: Level[] = [
  {
    n: 1,
    name: "Public",
    needs: [],
    needsLabel: "Published research, news and registries",
    unlocks: [
      "Market picture and patient funnel",
      "Draft personas, flagged for validation",
      "Competitor message map",
      "A first plan, costed on benchmarks",
    ],
    confidence: "Low — everything is external or estimated",
  },
  {
    n: 2,
    name: "Bought",
    needs: ["hcp_sample"],
    needsLabel: "A doctor file (HCP database)",
    unlocks: [
      "Segments sized on real doctor counts",
      "Eligibility filtering by specialty",
      "Target lists with a reason per doctor",
      "Rep-capacity check against the real field force",
    ],
    confidence: "Medium — potential is estimated from specialty and setting",
  },
  {
    n: 3,
    name: "Own",
    needs: ["engagement_events", "sales"],
    needsLabel: "Engagement logs and own sales",
    unlocks: [
      "Channel curves fitted to this brand, not pack priors",
      "Weekly next-best-action per doctor",
      "Engagement index as an early signal",
      "Measured lift — what the plan actually caused",
    ],
    confidence: "High, and rising each cycle as results come back",
  },
];

export function DataLevelPanel({ uploads }: { uploads: UploadInfo[] | undefined }) {
  const have = new Set((uploads ?? []).map((u) => u.kind));
  const met = (l: Level) => l.needs.every((k) => have.has(k));

  // The level reached is the highest one whose prerequisites are all met,
  // and every level below it too — connecting engagement logs without a
  // doctor file does not make the segments real.
  let reached = 1;
  for (const l of LEVELS) {
    if (met(l)) reached = Math.max(reached, l.n);
    else break;
  }
  const next = LEVELS.find((l) => l.n > reached);

  return (
    <Card
      title="What your data unlocks"
      sub="The engine never fills a missing input with a guess — it tells you what is still estimated instead"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 14 }}>
        {LEVELS.map((l) => {
          const active = l.n <= reached;
          return (
            <div
              key={l.n}
              style={{
                borderLeft: `3px solid ${active ? "var(--emerald)" : "var(--border-strong)"}`,
                background: active ? "var(--bg-surface)" : "var(--bg-raised)",
                border: "1px solid var(--border)",
                borderLeftWidth: 3,
                borderLeftColor: active ? "var(--emerald)" : "var(--border-strong)",
                borderRadius: "var(--radius-sm)",
                padding: 14,
                opacity: active ? 1 : 0.75,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
                {active ? (
                  <Check size={13} strokeWidth={3} style={{ color: "var(--emerald)" }} />
                ) : (
                  <Lock size={12} strokeWidth={2.4} style={{ color: "var(--text-3)" }} />
                )}
                <span style={{ fontSize: 13.5, fontWeight: 700, color: "var(--text-1)" }}>
                  Level {l.n} · {l.name}
                </span>
                {l.n === reached && (
                  <span
                    style={{
                      marginLeft: "auto",
                      background: "var(--gold)",
                      color: "var(--navy)",
                      borderRadius: "var(--radius-pill)",
                      padding: "1px 8px",
                      fontSize: 10,
                      fontWeight: 700,
                    }}
                  >
                    You are here
                  </span>
                )}
              </div>

              <div style={{ fontSize: 11.5, color: "var(--text-3)", marginBottom: 10, lineHeight: 1.5 }}>
                {l.needsLabel}
              </div>

              <ul
                style={{
                  listStyle: "disc outside",
                  paddingLeft: 16,
                  margin: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: 5,
                }}
              >
                {l.unlocks.map((u) => (
                  <li key={u} style={{ fontSize: 12, lineHeight: 1.5, color: "var(--text-2)", margin: 0 }}>
                    {u}
                  </li>
                ))}
              </ul>

              <div
                style={{
                  marginTop: 10,
                  paddingTop: 8,
                  borderTop: "1px solid var(--border)",
                  fontSize: 11,
                  color: "var(--text-3)",
                  lineHeight: 1.5,
                }}
              >
                {l.confidence}
              </div>
            </div>
          );
        })}
      </div>

      {next && (
        <div
          style={{
            marginTop: 14,
            borderLeft: "3px solid var(--gold)",
            background: "var(--gold-light)",
            borderRadius: "var(--radius-sm)",
            padding: "12px 14px",
          }}
        >
          <MicroLabel>To reach level {next.n}</MicroLabel>
          <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>
            Connect{" "}
            <strong>
              {next.needs
                .filter((k) => !have.has(k))
                .map((k) => k.replace(/_/g, " "))
                .join(" and ")}
            </strong>
            . Until then, {next.unlocks[0].toLowerCase()} stays out of reach and anything depending
            on it runs on pack defaults.
          </div>
        </div>
      )}
    </Card>
  );
}

import type { CSSProperties, ReactNode } from "react";
import { Maximize2 } from "lucide-react";

/* Shared primitives. Inline styles are the norm here; CSS classes in
   theme.css cover the shared shells (.card, .badge, .btn, .input,
   .pill-filter) and the tokens. */

/* ---------------- Card ---------------- */

export function Card({
  children,
  clickable,
  onClick,
  style,
  title,
  right,
  sub,
}: {
  children?: ReactNode;
  clickable?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
  title?: ReactNode;
  right?: ReactNode;
  sub?: string;
}) {
  const header = (title || right) && (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        gap: 12,
        marginBottom: 14,
      }}
    >
      <div style={{ minWidth: 0 }}>
        {title && <h2>{title}</h2>}
        {sub && (
          <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--text-3)" }}>{sub}</p>
        )}
      </div>
      {right && <div style={{ flexShrink: 0, display: "flex", gap: 8 }}>{right}</div>}
    </div>
  );

  if (clickable) {
    return (
      <div
        className="card card-clickable"
        role="button"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onClick?.();
          }
        }}
        style={{ position: "relative", cursor: "pointer", ...style }}
      >
        <Maximize2
          size={13}
          strokeWidth={2.2}
          style={{ position: "absolute", top: 16, right: 16, color: "var(--text-3)", opacity: 0.6 }}
        />
        {header}
        {children}
      </div>
    );
  }

  return (
    <div className="card" style={style}>
      {header}
      {children}
    </div>
  );
}

/* ---------------- Badge ---------------- */

export type BadgeColor =
  | "emerald"
  | "amber"
  | "red"
  | "blue"
  | "teal"
  | "navy"
  | "gold"
  | "navySoft"
  | "neutral";

const BADGE_STYLES: Record<BadgeColor, CSSProperties> = {
  emerald: { background: "var(--emerald-bg)", color: "var(--emerald-text)" },
  amber: { background: "var(--amber-bg)", color: "var(--amber-text)" },
  red: { background: "var(--red-bg)", color: "var(--red-text)" },
  blue: { background: "var(--blue-bg)", color: "var(--blue-text)" },
  teal: { background: "var(--teal-bg)", color: "var(--teal-text)" },
  navy: { background: "var(--navy)", color: "var(--text-inv)" },
  gold: { background: "var(--gold)", color: "var(--navy)" },
  navySoft: { background: "var(--navy-faint)", color: "var(--navy)" },
  neutral: { background: "var(--bg-raised)", color: "var(--text-3)" },
};

export function Badge({
  color = "neutral",
  children,
  style,
}: {
  color?: BadgeColor;
  children: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <span className="badge" style={{ ...BADGE_STYLES[color], ...style }}>
      {children}
    </span>
  );
}

export function DemoBadge() {
  return <Badge color="gold">AI-generated demo</Badge>;
}

/* ---------------- Pill (segmented filter) ---------------- */

export function Pill({
  active,
  onClick,
  children,
}: {
  active?: boolean;
  onClick?: () => void;
  children: ReactNode;
}) {
  return (
    <button type="button" className={`pill-filter${active ? " active" : ""}`} onClick={onClick}>
      {children}
    </button>
  );
}

/* ---------------- SectionHeading ---------------- */

export function SectionHeading({
  eyebrow,
  title,
  sub,
  right,
}: {
  eyebrow?: string;
  title: string;
  sub?: string;
  right?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div style={{ minWidth: 0 }}>
        {eyebrow && <div className="page-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {right && <div style={{ flexShrink: 0 }}>{right}</div>}
    </div>
  );
}

/* ---------------- AccentCallout ---------------- */

const CALLOUT_TONES = {
  gold: { border: "var(--gold)", bg: "var(--gold-light)", label: "var(--gold-muted)" },
  navy: { border: "var(--navy)", bg: "var(--navy-faint)", label: "var(--navy)" },
  red: { border: "var(--red)", bg: "var(--red-bg)", label: "var(--red-text)" },
  emerald: { border: "var(--emerald)", bg: "var(--emerald-bg)", label: "var(--emerald-text)" },
} as const;

export function AccentCallout({
  label,
  tone = "navy",
  icon,
  children,
  style,
}: {
  label?: string;
  tone?: keyof typeof CALLOUT_TONES;
  icon?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
}) {
  const t = CALLOUT_TONES[tone];
  return (
    <div
      style={{
        borderLeft: `3px solid ${t.border}`,
        background: t.bg,
        borderRadius: "var(--radius-sm)",
        padding: "12px 16px",
        ...style,
      }}
    >
      {label && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 10.5,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.07em",
            color: t.label,
            marginBottom: 6,
          }}
        >
          {icon}
          {label}
        </div>
      )}
      <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{children}</div>
    </div>
  );
}

/* ---------------- MetricStat ---------------- */

export function MetricStat({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "navy" | "gold" | "emerald" | "red";
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
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
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
      <div
        className="tabular"
        style={{ fontSize: 26, fontWeight: 700, lineHeight: 1.1, color, letterSpacing: "-0.01em" }}
      >
        {value}
      </div>
      {sub && <div style={{ fontSize: 11.5, color: "var(--text-3)" }}>{sub}</div>}
    </div>
  );
}

/* ---------------- AvatarInitials ---------------- */

export function AvatarInitials({
  text,
  size = 36,
  gold,
  photoUrl,
}: {
  text: string;
  size?: number;
  gold?: boolean;
  photoUrl?: string | null;
}) {
  const initials = text
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt=""
        style={{ width: size, height: size, borderRadius: "50%", objectFit: "cover", flexShrink: 0 }}
      />
    );
  }

  return (
    <div
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        flexShrink: 0,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: gold ? "var(--gold-light)" : "var(--navy-faint)",
        color: gold ? "var(--gold-muted)" : "var(--navy)",
        border: `1px solid ${gold ? "var(--gold-pale)" : "var(--navy-subtle)"}`,
        fontSize: size * 0.36,
        fontWeight: 700,
        letterSpacing: "0.02em",
      }}
    >
      {initials || "—"}
    </div>
  );
}

/* ---------------- EmptyState ---------------- */

export function EmptyState({
  icon,
  title,
  sub,
  children,
  action,
}: {
  icon?: ReactNode;
  title?: string;
  sub?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div
      style={{
        padding: "40px 24px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      {icon && <div style={{ color: "var(--text-3)", opacity: 0.6 }}>{icon}</div>}
      {title && <div style={{ fontWeight: 700, fontSize: 13.5, color: "var(--text-2)" }}>{title}</div>}
      <div style={{ fontSize: 12.5, color: "var(--text-3)", maxWidth: 460, lineHeight: 1.6 }}>
        {sub ?? children}
      </div>
      {action && <div style={{ marginTop: 6 }}>{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Unable to load this data",
  children,
  action,
}: {
  title?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="error-state">
      <div className="error-state-title">{title}</div>
      <p>{children}</p>
      {action}
    </div>
  );
}

/* ---------------- ConfidencePill ---------------- */

export function ConfidencePill({ level }: { level: "High" | "Medium" | "Low" | number }) {
  const label =
    typeof level === "number"
      ? level >= 0.75
        ? "High"
        : level >= 0.5
        ? "Medium"
        : "Low"
      : level;
  const color: BadgeColor = label === "High" ? "emerald" : label === "Medium" ? "amber" : "red";
  return (
    <Badge color={color}>
      {typeof level === "number" ? `${label} · ${(level * 100).toFixed(0)}%` : `${label} confidence`}
    </Badge>
  );
}

/* ---------------- Numbered step section (§5.7) ---------------- */

export function StepHeading({ n, title, right }: { n: number; title: string; right?: ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: 7,
          background: "var(--navy)",
          color: "var(--text-inv)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          fontWeight: 700,
          flexShrink: 0,
        }}
      >
        {n}
      </div>
      <div
        style={{
          fontSize: 11.5,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          color: "var(--navy)",
          flex: 1,
        }}
      >
        {title}
      </div>
      {right}
    </div>
  );
}

/* ---------------- Micro label + field ---------------- */

export function MicroLabel({ children }: { children: ReactNode }) {
  return (
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
      {children}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <MicroLabel>{label}</MicroLabel>
      <div style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-2)" }}>{children}</div>
    </div>
  );
}

/* ---------------- Bullet list (markers always re-enabled, §5.2) ---------------- */

export function BulletList({
  items,
  style,
  size = 13,
}: {
  items: string[];
  style?: CSSProperties;
  size?: number;
}) {
  if (!items.length) return null;
  return (
    <ul
      style={{
        listStyle: "disc outside",
        paddingLeft: 18,
        margin: 0,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        ...style,
      }}
    >
      {items.map((it, i) => (
        <li key={i} style={{ fontSize: size, lineHeight: 1.6, color: "var(--text-2)", margin: 0 }}>
          {it}
        </li>
      ))}
    </ul>
  );
}

/* ---------------- Table shell (§5.6) ---------------- */

export function TableWrap({ minWidth = 640, children }: { minWidth?: number; children: ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table" style={{ minWidth }}>
        {children}
      </table>
    </div>
  );
}

import type { Status, Rag } from "../api/types";

export function StatusBadge({ status }: { status: Status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export function RagPill({ rag }: { rag: Rag | null }) {
  if (!rag) return <span className="badge badge-draft">—</span>;
  return <span className={`badge rag-pill ${rag === "green" ? "" : rag}`}>{rag}</span>;
}

export function ConfidenceBadge({
  source,
  origin,
  as_of,
  confidence,
}: {
  source: string;
  origin: string;
  as_of: string;
  confidence: number;
}) {
  return (
    <span
      className="confidence-badge"
      title={`source: ${source}\norigin: ${origin}\nas of: ${as_of}`}
    >
      conf {(confidence * 100).toFixed(0)}%
    </span>
  );
}

export function EvidenceChip({ count }: { count: number }) {
  if (!count) return null;
  return <span className="evidence-chip">{count} evidence</span>;
}

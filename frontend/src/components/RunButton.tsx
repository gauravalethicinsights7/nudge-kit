import { Play } from "lucide-react";
import { ApiError } from "../api/client";

export function RunButton({
  label,
  onRun,
  isPending,
  disabledReason,
  error,
  primary = true,
}: {
  label: string;
  onRun: () => void;
  isPending: boolean;
  disabledReason?: string | null;
  error?: unknown;
  primary?: boolean;
}) {
  const errorDetail = error instanceof ApiError ? error.detail : error ? String(error) : null;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
      <button
        className={primary ? "btn-navy" : "btn-ghost"}
        onClick={onRun}
        disabled={isPending || !!disabledReason}
        title={disabledReason ?? undefined}
      >
        {!isPending && <Play size={12} style={{ marginRight: 6, verticalAlign: "-1px" }} />}
        {isPending ? "Running…" : label}
      </button>
      {disabledReason && (
        <span style={{ fontSize: 11, color: "var(--text-3)", maxWidth: 260, textAlign: "right", lineHeight: 1.5 }}>
          {disabledReason}
        </span>
      )}
      {errorDetail && (
        <span style={{ fontSize: 11, color: "var(--red-text)", maxWidth: 280, textAlign: "right", lineHeight: 1.5 }}>
          {errorDetail}
        </span>
      )}
    </div>
  );
}

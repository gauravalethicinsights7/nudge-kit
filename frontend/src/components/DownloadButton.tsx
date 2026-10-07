import { useState } from "react";
import { downloadWithAuth } from "../api/client";

export function DownloadButton({ path, filename, label }: { path: string; filename: string; label: string }) {
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onClick = async () => {
    setIsPending(true);
    setError(null);
    try {
      await downloadWithAuth(path, filename);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsPending(false);
    }
  };

  return (
    <span style={{ display: "inline-flex", flexDirection: "column", alignItems: "flex-end" }}>
      <button className="btn" onClick={onClick} disabled={isPending}>
        {isPending ? "Downloading…" : label}
      </button>
      {error && <span style={{ fontSize: 11, color: "var(--color-red)" }}>{error}</span>}
    </span>
  );
}

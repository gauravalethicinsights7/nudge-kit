import { useEffect } from "react";
import type { ReactNode } from "react";

// Right-side slide-over for drill-down detail (spec §26) — keeps the user's
// list/chart context intact instead of navigating to a new page.
export function Drawer({
  open,
  onClose,
  title,
  subtitle,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <div className="drawer-panel" role="dialog" aria-modal="true" aria-label={title}>
        <div className="drawer-header">
          <div>
            <div className="drawer-title">{title}</div>
            {subtitle && <div className="drawer-subtitle">{subtitle}</div>}
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            &#10005;
          </button>
        </div>
        <div className="drawer-body">{children}</div>
      </div>
    </>
  );
}

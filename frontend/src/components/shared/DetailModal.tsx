import { useEffect } from "react";
import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

// Centered detail surface: gold top border, Playfair title, Esc/backdrop
// close, body scroll locked while open.
export function DetailModal({
  open,
  onClose,
  title,
  eyebrow,
  right,
  width = 680,
  contentMaxHeight = "68vh",
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  eyebrow?: string;
  right?: ReactNode;
  width?: number;
  contentMaxHeight?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
        style={{ width, maxWidth: "94vw" }}
      >
        <div className="modal-header">
          <div style={{ minWidth: 0 }}>
            {eyebrow && <div className="page-eyebrow" style={{ marginBottom: 4 }}>{eyebrow}</div>}
            <h2 className="modal-title">{title}</h2>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            {right}
            <button className="modal-close" onClick={onClose} aria-label="Close">
              <X size={16} />
            </button>
          </div>
        </div>
        <div className="modal-body" style={{ maxHeight: contentMaxHeight }}>
          {children}
        </div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}

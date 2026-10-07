import { Link } from "react-router-dom";

export interface Crumb {
  label: string;
  to?: string;
}

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={i} style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
          {i > 0 && <span className="crumb-sep">/</span>}
          {item.to && i < items.length - 1 ? (
            <Link to={item.to}>{item.label}</Link>
          ) : (
            <span className="crumb-current">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

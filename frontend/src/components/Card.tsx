import type { ReactNode } from "react";
import { SectionHeading } from "./shared/ui";

export { Card, EmptyState, ErrorState, SectionHeading } from "./shared/ui";

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  right,
  eyebrow,
}: {
  title: string;
  description?: string;
  right?: ReactNode;
  eyebrow?: string;
}) {
  return <SectionHeading eyebrow={eyebrow} title={title} sub={description} right={right} />;
}

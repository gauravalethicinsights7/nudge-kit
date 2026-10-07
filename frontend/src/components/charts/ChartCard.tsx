import type { ReactNode } from "react";
import { Skeleton } from "../Skeleton";

export function ChartCard({
  title,
  subtitle,
  right,
  height = 240,
  isLoading,
  isEmpty,
  emptyMessage = "No data for the current selection.",
  children,
}: {
  title: string;
  subtitle?: string;
  right?: ReactNode;
  height?: number;
  isLoading?: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  children: ReactNode;
}) {
  return (
    <div className="card" style={{ marginBottom: 0, height: "100%" }}>
      <div className="chart-card-header">
        <div>
          <h2 className="chart-title">{title}</h2>
          {subtitle && <div className="chart-subtitle">{subtitle}</div>}
        </div>
        {right}
      </div>
      {isLoading ? (
        <Skeleton height={height} />
      ) : isEmpty ? (
        <div className="chart-empty" style={{ height }}>{emptyMessage}</div>
      ) : (
        children
      )}
    </div>
  );
}

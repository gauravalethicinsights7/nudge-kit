export function Skeleton({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} height={12} width={i === lines - 1 ? "60%" : "100%"} />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} style={{ display: "flex", gap: 16 }}>
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} height={12} width={c === 0 ? "22%" : "16%"} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonKpiRow({ count = 4 }: { count?: number }) {
  return (
    <div className={`grid grid-${count}`} style={{ marginBottom: 18 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="kpi-card">
          <Skeleton height={11} width="50%" />
          <Skeleton height={28} width="70%" />
          <Skeleton height={11} width="40%" />
        </div>
      ))}
    </div>
  );
}

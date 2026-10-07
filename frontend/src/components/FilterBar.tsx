// Visible, reversible filters with a "Clear all" (spec §27).
export function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="filter-chip">
      {label}
      <button onClick={onRemove} aria-label={`Remove filter: ${label}`}>&#10005;</button>
    </span>
  );
}

export function FilterBar({
  chips,
  onClearAll,
}: {
  chips: { key: string; label: string; onRemove: () => void }[];
  onClearAll: () => void;
}) {
  if (!chips.length) return null;
  return (
    <div className="filter-bar">
      {chips.map((c) => (
        <FilterChip key={c.key} label={c.label} onRemove={c.onRemove} />
      ))}
      <span className="filter-clear-all" onClick={onClearAll}>Clear all</span>
    </div>
  );
}

import type { ReactNode } from "react";
import { EmptyState } from "./Card";

export interface Column<T> {
  header: string;
  render: (row: T) => ReactNode;
  key: string;
}

export function DataTable<T>({
  rows,
  columns,
  emptyMessage,
  rowKey,
}: {
  rows: T[];
  columns: Column<T>[];
  emptyMessage: string;
  rowKey: (row: T) => string;
}) {
  if (!rows.length) return <EmptyState>{emptyMessage}</EmptyState>;
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((c) => (
                <td key={c.key}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

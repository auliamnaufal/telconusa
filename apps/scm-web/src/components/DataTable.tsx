import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[] | null;
  rowKey: (row: T) => string;
  empty?: string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T extends Record<string, unknown>>({ columns, rows, rowKey, empty = "Belum ada data.", onRowClick }: Props<T>) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={`px-4 py-2.5 font-semibold ${column.className ?? ""}`}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows === null && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-6 text-center text-slate-500">
                Memuat...
              </td>
            </tr>
          )}
          {rows !== null && rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-6 text-center text-slate-500">
                {empty}
              </td>
            </tr>
          )}
          {rows?.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={onRowClick ? "cursor-pointer hover:bg-slate-50" : undefined}
            >
              {columns.map((column) => (
                <td key={column.key} className={`px-4 py-2.5 ${column.className ?? ""}`}>
                  {column.render ? column.render(row) : (row[column.key] as ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

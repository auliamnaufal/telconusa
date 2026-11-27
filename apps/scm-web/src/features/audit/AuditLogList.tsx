"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { inputClass } from "@/components/Field";
import { useToast } from "@/components/Toast";
import { ENTITIES, listAuditLogs, type AuditFilters, type AuditLogEntry } from "./api";

const LIMIT = 20;

function formatTime(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Jakarta" }).format(new Date(value));
}

export function AuditLogList() {
  const toast = useToast();
  const [filters, setFilters] = useState<AuditFilters>({ entity: "", entity_id: "", actor: "", page: 1, limit: LIMIT });
  const [rows, setRows] = useState<AuditLogEntry[] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setRows(null);
    listAuditLogs(filters, controller.signal)
      .then(setRows)
      .catch((error) => {
        if (error?.name !== "AbortError") {
          toast.error(error);
          setRows([]);
        }
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  function update(patch: Partial<AuditFilters>) {
    setFilters((current) => ({ ...current, ...patch, page: patch.page ?? 1 }));
  }

  const columns: Column<AuditLogEntry>[] = [
    { key: "at", header: "Waktu", className: "whitespace-nowrap", render: (row) => formatTime(row.at) },
    {
      key: "actor",
      header: "Pelaku",
      render: (row) => (
        <span>
          <span className="font-mono-num font-semibold">{row.actor}</span>
          {row.role && <span className="ml-1 text-xs text-slate-500">({row.role})</span>}
        </span>
      ),
    },
    { key: "action", header: "Aksi", className: "font-mono-num" },
    { key: "entity", header: "Entitas", render: (row) => `${row.entity} · ${row.entity_id}` },
    { key: "correlation_id", header: "Correlation ID", className: "font-mono-num", render: (row) => row.correlation_id ?? "-" },
    {
      key: "detail",
      header: "Detail",
      render: (row) =>
        row.detail ? (
          <details>
            <summary className="cursor-pointer text-xs font-semibold text-slate-600">Lihat</summary>
            <pre className="mt-1 max-w-md overflow-x-auto whitespace-pre-wrap rounded bg-slate-50 p-2 text-[11px] text-slate-700">
              {JSON.stringify(row.detail, null, 2)}
            </pre>
          </details>
        ) : (
          "-"
        ),
    },
  ];

  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">Audit</h1>
      <p className="mt-1 text-sm text-slate-500">Jejak operasi tulis SCM: siapa, kapan, aksi apa, dan correlation ID-nya.</p>

      <div className="mt-6 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Entitas</span>
          <select className={inputClass} value={filters.entity} onChange={(e) => update({ entity: e.target.value })}>
            <option value="">Semua</option>
            {ENTITIES.map((entity) => (
              <option key={entity} value={entity}>
                {entity}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">ID entitas</span>
          <input className={inputClass} placeholder="SR-2026-000001" value={filters.entity_id} onChange={(e) => update({ entity_id: e.target.value })} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Pelaku</span>
          <input className={inputClass} placeholder="EMP-0001" value={filters.actor} onChange={(e) => update({ actor: e.target.value })} />
        </label>
      </div>

      <div className="mt-4">
        <DataTable
          columns={columns}
          rows={rows as (AuditLogEntry & Record<string, unknown>)[] | null}
          rowKey={(row) => row.id}
          empty="Belum ada catatan audit untuk filter ini."
        />
      </div>

      <div className="mt-4 flex items-center justify-end gap-2 text-sm text-slate-600">
        <Button variant="secondary" disabled={filters.page <= 1} onClick={() => update({ page: filters.page - 1 })}>
          Sebelumnya
        </Button>
        <span>Halaman {filters.page}</span>
        <Button variant="secondary" disabled={!rows || rows.length < LIMIT} onClick={() => update({ page: filters.page + 1 })}>
          Berikutnya
        </Button>
      </div>
    </div>
  );
}

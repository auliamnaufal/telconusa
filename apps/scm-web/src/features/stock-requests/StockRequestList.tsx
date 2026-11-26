"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { inputClass } from "@/components/Field";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import { listStockRequests } from "./api";
import { CITIES, STATUSES, type ListFilters, type StockRequestSummary } from "./types";

const LIMIT = 20;

export function StockRequestList() {
  const router = useRouter();
  const toast = useToast();
  const [filters, setFilters] = useState<ListFilters>({ status: "", city_code: "", ticket_code: "", page: 1, limit: LIMIT });
  const [rows, setRows] = useState<StockRequestSummary[] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setRows(null);
    listStockRequests(filters, controller.signal)
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

  function update(patch: Partial<ListFilters>) {
    setFilters((current) => ({ ...current, ...patch, page: patch.page ?? 1 }));
  }

  const columns: Column<StockRequestSummary>[] = [
    { key: "stock_request_no", header: "No. permintaan", className: "font-mono-num font-semibold" },
    { key: "ticket_code", header: "Tiket", className: "font-mono-num" },
    { key: "city_code", header: "Kota" },
    { key: "technician_employee_id", header: "Teknisi", render: (row) => row.technician_employee_id ?? "-" },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span className="flex flex-wrap items-center gap-2">
          <StatusBadge status={row.status} />
          {row.return_pending && (
            <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
              return pending
            </span>
          )}
        </span>
      ),
    },
  ];

  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">Permintaan Barang</h1>
      <p className="mt-1 text-sm text-slate-500">Permintaan barang otomatis dari tiket CRM. Pilih baris untuk membuka detail.</p>

      <div className="mt-6 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Status</span>
          <select className={inputClass} value={filters.status} onChange={(e) => update({ status: e.target.value })}>
            <option value="">Semua</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Kota</span>
          <select className={inputClass} value={filters.city_code} onChange={(e) => update({ city_code: e.target.value })}>
            <option value="">Semua</option>
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Kode tiket</span>
          <input
            className={inputClass}
            placeholder="TKT-000001"
            value={filters.ticket_code}
            onChange={(e) => update({ ticket_code: e.target.value })}
          />
        </label>
      </div>

      <div className="mt-4">
        <DataTable
          columns={columns}
          rows={rows as (StockRequestSummary & Record<string, unknown>)[] | null}
          rowKey={(row) => row.stock_request_no}
          empty="Tidak ada permintaan barang untuk filter ini."
          onRowClick={(row) => router.push(`/stock-requests/${row.stock_request_no}`)}
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

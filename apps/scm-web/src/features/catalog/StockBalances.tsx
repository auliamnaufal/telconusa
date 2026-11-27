"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { inputClass } from "@/components/Field";
import { useToast } from "@/components/Toast";
import { listBalances, listItems, listWarehouses, type BalanceFilters, type Item, type StockBalance, type Warehouse } from "./api";

const LIMIT = 20;
const number = new Intl.NumberFormat("id-ID");

export function StockBalances() {
  const toast = useToast();
  const [filters, setFilters] = useState<BalanceFilters>({ warehouse_code: "", item_sku: "", page: 1, limit: LIMIT });
  const [rows, setRows] = useState<StockBalance[] | null>(null);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [items, setItems] = useState<Item[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([listWarehouses(controller.signal), listItems(controller.signal)])
      .then(([w, i]) => {
        setWarehouses(w);
        setItems(i);
      })
      .catch((error) => error?.name !== "AbortError" && toast.error(error));
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setRows(null);
    listBalances(filters, controller.signal)
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

  function update(patch: Partial<BalanceFilters>) {
    setFilters((current) => ({ ...current, ...patch, page: patch.page ?? 1 }));
  }

  const qty = (value: number) => number.format(value);
  const columns: Column<StockBalance>[] = [
    { key: "warehouse_code", header: "Gudang", className: "whitespace-nowrap font-mono-num" },
    {
      key: "item_sku",
      header: "Barang",
      className: "min-w-44",
      render: (row) => (
        <span>
          <span className="whitespace-nowrap font-mono-num font-semibold">{row.item_sku}</span>
          <span className="block text-xs text-slate-500">{row.name}</span>
        </span>
      ),
    },
    { key: "qty_physical", header: "Fisik", className: "text-right font-mono-num", render: (row) => qty(row.qty_physical) },
    { key: "qty_reserved", header: "Reservasi", className: "text-right font-mono-num", render: (row) => qty(row.qty_reserved) },
    {
      key: "qty_damaged",
      header: "Rusak",
      className: "text-right font-mono-num",
      render: (row) => <span className={row.qty_damaged > 0 ? "font-semibold text-rose-700" : undefined}>{qty(row.qty_damaged)}</span>,
    },
    {
      key: "qty_available",
      header: "Tersedia",
      className: "text-right font-mono-num font-semibold",
      render: (row) => `${qty(row.qty_available)} ${row.unit}`,
    },
    { key: "reorder_point", header: "ROP", className: "text-right font-mono-num", render: (row) => qty(row.reorder_point) },
    {
      key: "below_rop",
      header: "Status stok",
      render: (row) =>
        row.below_rop ? (
          <span className="rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">di bawah ROP</span>
        ) : (
          <span className="text-xs text-slate-500">aman</span>
        ),
    },
  ];

  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">Stok</h1>
      <p className="mt-1 text-sm text-slate-500">
        Saldo per gudang dan barang. Tersedia = fisik − reservasi − rusak; barang rusak dicatat terpisah dan tidak bisa dikeluarkan.
      </p>

      <div className="mt-6 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Gudang</span>
          <select className={inputClass} value={filters.warehouse_code} onChange={(e) => update({ warehouse_code: e.target.value })}>
            <option value="">Semua</option>
            {warehouses.map((w) => (
              <option key={w.code} value={w.code}>
                {w.code} · {w.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-semibold text-slate-700">Barang</span>
          <select className={inputClass} value={filters.item_sku} onChange={(e) => update({ item_sku: e.target.value })}>
            <option value="">Semua</option>
            {items.map((i) => (
              <option key={i.sku} value={i.sku}>
                {i.sku} · {i.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4">
        <DataTable
          columns={columns}
          rows={rows as (StockBalance & Record<string, unknown>)[] | null}
          rowKey={(row) => `${row.warehouse_code}:${row.item_sku}`}
          empty="Tidak ada saldo untuk filter ini."
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

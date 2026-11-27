"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { useToast } from "@/components/Toast";
import { formatIDR, getAuth } from "@/lib/auth";
import { listItems, listPackageKits, listVendors, listWarehouses, type Item, type PackageKit, type Vendor, type Warehouse } from "./api";
import { ItemForm, KitForm, VendorForm } from "./forms";

type Tab = "items" | "warehouses" | "vendors" | "kits";
const TABS: { id: Tab; label: string }[] = [
  { id: "items", label: "Barang" },
  { id: "warehouses", label: "Gudang" },
  { id: "vendors", label: "Vendor" },
  { id: "kits", label: "Daftar barang paket" },
];

type Editing =
  | { kind: "item"; value: Item | null }
  | { kind: "vendor"; value: Vendor | null }
  | { kind: "kit"; value: PackageKit | null }
  | null;

interface Data {
  items: Item[];
  warehouses: Warehouse[];
  vendors: Vendor[];
  kits: PackageKit[];
}

export function Catalog() {
  const toast = useToast();
  const canEdit = getAuth().user?.role === "SCM_MANAGER";
  const [tab, setTab] = useState<Tab>("items");
  const [data, setData] = useState<Data | null>(null);
  const [editing, setEditing] = useState<Editing>(null);

  const load = useCallback(
    (signal?: AbortSignal) =>
      Promise.all([listItems(signal), listWarehouses(signal), listVendors(signal), listPackageKits(signal)])
        .then(([items, warehouses, vendors, kits]) => setData({ items, warehouses, vendors, kits }))
        .catch((error) => {
          if (error?.name !== "AbortError") {
            toast.error(error);
            setData({ items: [], warehouses: [], vendors: [], kits: [] });
          }
        }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  function done() {
    setEditing(null);
    load();
  }

  const editColumn = <T,>(onEdit: (row: T) => void): Column<T>[] =>
    canEdit
      ? [
          {
            key: "_edit",
            header: "",
            className: "text-right",
            render: (row) => (
              <Button variant="secondary" onClick={() => onEdit(row)}>
                Ubah
              </Button>
            ),
          },
        ]
      : [];

  const itemColumns: Column<Item>[] = [
    { key: "sku", header: "SKU", className: "whitespace-nowrap font-mono-num font-semibold" },
    { key: "name", header: "Nama" },
    { key: "unit", header: "Satuan" },
    { key: "unit_cost", header: "Harga satuan", className: "text-right font-mono-num", render: (row) => formatIDR(row.unit_cost) },
    { key: "reorder_point", header: "ROP/gudang", className: "text-right font-mono-num" },
    { key: "safety_stock", header: "Stok pengaman", className: "text-right font-mono-num" },
    { key: "is_serialized", header: "Nomor seri", render: (row) => (row.is_serialized ? "Ya" : "Tidak") },
    ...editColumn<Item>((row) => setEditing({ kind: "item", value: row })),
  ];

  const warehouseColumns: Column<Warehouse>[] = [
    { key: "code", header: "Kode", className: "font-mono-num font-semibold" },
    { key: "name", header: "Nama" },
    { key: "city_code", header: "Kota dilayani", className: "font-mono-num" },
  ];

  const vendorColumns: Column<Vendor>[] = [
    { key: "code", header: "Kode", className: "font-mono-num font-semibold" },
    { key: "name", header: "Nama" },
    { key: "category", header: "Kategori", className: "font-mono-num" },
    { key: "rating_score", header: "Rating", className: "text-right font-mono-num", render: (row) => row.rating_score?.toFixed(2) ?? "-" },
    ...editColumn<Vendor>((row) => setEditing({ kind: "vendor", value: row })),
  ];

  const kitColumns: Column<PackageKit>[] = [
    { key: "service_sku", header: "Paket layanan", className: "font-mono-num font-semibold" },
    {
      key: "items",
      header: "Barang",
      render: (row) => (
        <ul className="space-y-0.5">
          {row.items.map((line) => (
            <li key={line.item_sku}>
              <span className="font-mono-num">{line.qty} {line.unit}</span> · {line.item_sku} <span className="text-slate-500">({line.name})</span>
            </li>
          ))}
        </ul>
      ),
    },
    ...editColumn<PackageKit>((row) => setEditing({ kind: "kit", value: row })),
  ];

  const addLabel: Partial<Record<Tab, string>> = { items: "Tambah barang", vendors: "Tambah vendor", kits: "Tambah daftar paket" };

  function add() {
    if (tab === "items") setEditing({ kind: "item", value: null });
    if (tab === "vendors") setEditing({ kind: "vendor", value: null });
    if (tab === "kits") setEditing({ kind: "kit", value: null });
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">Katalog</h1>
      <p className="mt-1 text-sm text-slate-500">
        Data master barang, gudang, vendor, dan daftar barang per paket layanan.
        {!canEdit && " Hanya Manajer SCM yang dapat mengubah data."}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200">
        <div className="flex gap-1" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`-mb-px cursor-pointer border-b-2 px-3 py-2 text-sm font-semibold ${
                tab === t.id ? "border-[#E11D2E] text-slate-900" : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        {canEdit && addLabel[tab] && (
          <Button className="mb-2" onClick={add}>
            {addLabel[tab]}
          </Button>
        )}
      </div>

      <div className="mt-4">
        {tab === "items" && (
          <DataTable columns={itemColumns} rows={(data?.items ?? null) as (Item & Record<string, unknown>)[] | null} rowKey={(r) => r.sku} />
        )}
        {tab === "warehouses" && (
          <DataTable
            columns={warehouseColumns}
            rows={(data?.warehouses ?? null) as (Warehouse & Record<string, unknown>)[] | null}
            rowKey={(r) => r.code}
          />
        )}
        {tab === "vendors" && (
          <DataTable columns={vendorColumns} rows={(data?.vendors ?? null) as (Vendor & Record<string, unknown>)[] | null} rowKey={(r) => r.code} />
        )}
        {tab === "kits" && (
          <DataTable
            columns={kitColumns}
            rows={(data?.kits ?? null) as (PackageKit & Record<string, unknown>)[] | null}
            rowKey={(r) => r.service_sku}
            empty="Belum ada daftar barang paket."
          />
        )}
      </div>

      {editing?.kind === "item" && <ItemForm initial={editing.value} onClose={() => setEditing(null)} onDone={done} />}
      {editing?.kind === "vendor" && <VendorForm initial={editing.value} onClose={() => setEditing(null)} onDone={done} />}
      {editing?.kind === "kit" && data && <KitForm initial={editing.value} items={data.items} onClose={() => setEditing(null)} onDone={done} />}
    </div>
  );
}

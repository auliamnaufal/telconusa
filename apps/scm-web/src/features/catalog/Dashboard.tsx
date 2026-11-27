"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DataTable, type Column } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import { formatIDR, getAuth } from "@/lib/auth";
import { canAccess } from "@/lib/roles";
import { getDashboardSummary, type DashboardSummary } from "./api";

type RecentRow = DashboardSummary["stock_requests"][number];

function Card({ label, value, hint, tone = "slate" }: { label: string; value: string | number; hint?: string; tone?: "slate" | "amber" | "blue" | "green" }) {
  const accent = { slate: "border-t-slate-300", amber: "border-t-amber-400", blue: "border-t-sky-500", green: "border-t-emerald-500" }[tone];
  return (
    <div className={`rounded-xl border border-slate-200 border-t-4 bg-white p-4 ${accent}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 font-display text-2xl font-extrabold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export function Dashboard() {
  const toast = useToast();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [failed, setFailed] = useState(false);
  const role = getAuth().user?.role;
  const canOpenRequests = canAccess(role, "/stock-requests");

  useEffect(() => {
    const controller = new AbortController();
    getDashboardSummary(controller.signal)
      .then(setSummary)
      .catch((error) => {
        if (error?.name !== "AbortError") {
          toast.error(error);
          setFailed(true);
        }
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const columns: Column<RecentRow>[] = [
    {
      key: "stock_request_no",
      header: "No. permintaan",
      className: "font-mono-num font-semibold",
      render: (row) =>
        canOpenRequests ? (
          <Link className="text-[#E11D2E] hover:underline" href={`/stock-requests/${row.stock_request_no}`}>
            {row.stock_request_no}
          </Link>
        ) : (
          row.stock_request_no
        ),
    },
    { key: "ticket_code", header: "Tiket", className: "font-mono-num" },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  ];

  const k = summary?.kpis;
  return (
    <div>
      <h1 className="font-display text-2xl font-extrabold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Ringkasan persediaan, reservasi, pengadaan, dan aset ONT.</p>

      {failed && !summary && <p className="mt-6 text-sm text-rose-700">Ringkasan dashboard gagal dimuat.</p>}
      {!failed && !summary && <p className="mt-6 text-sm text-slate-500">Memuat...</p>}

      {k && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Card label="Stok tersedia (nilai persediaan)" value={formatIDR(k.inventory_valuation_idr)} hint={`${k.total_skus} SKU; barang rusak tidak dihitung`} tone="green" />
          <Card label="Reservasi aktif" value={k.active_reservations} hint="Permintaan barang READY_TO_ISSUE" tone="amber" />
          <Card label="PO terbuka" value={k.open_purchase_orders} hint="Belum diterima penuh atau ditutup" tone="blue" />
          <Card label="ONT terpasang" value={k.ont_installed} hint="Unit berstatus INSTALLED" tone="green" />
          <Card label="Retur tertunda" value={k.return_pending} hint="Sudah dikeluarkan, laporan pemakaian belum masuk" tone="amber" />
          <Card label="Permintaan barang terbuka" value={k.open_stock_requests} hint="REQUESTED, PENDING_STOCK, READY_TO_ISSUE, ISSUED" />
        </div>
      )}

      {summary && (
        <section className="mt-8">
          <h2 className="font-display text-lg font-bold text-slate-900">Permintaan barang terbaru</h2>
          <div className="mt-3">
            <DataTable
              columns={columns}
              rows={summary.stock_requests as (RecentRow & Record<string, unknown>)[]}
              rowKey={(row) => row.stock_request_no}
              empty="Belum ada permintaan barang."
            />
          </div>
        </section>
      )}
    </div>
  );
}

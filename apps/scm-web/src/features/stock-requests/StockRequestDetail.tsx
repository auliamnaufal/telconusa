"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import { getAuth } from "@/lib/auth";
import { CancelDialog, DamagedDialog, ExtraDialog, IssueDialog } from "./actions";
import { getStockRequest } from "./api";
import { WAREHOUSE_ROLES, type StockRequestDetail as Detail, type StockRequestLine } from "./types";

type Dialog = "issue" | "extra" | "damaged" | "cancel" | null;

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" }) : "-";
}

function Info({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold text-slate-900">{children}</dd>
    </div>
  );
}

export function StockRequestDetail({ stockRequestNo }: { stockRequestNo: string }) {
  const toast = useToast();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [dialog, setDialog] = useState<Dialog>(null);
  const role = getAuth().user?.role ?? "";
  const canAct = WAREHOUSE_ROLES.includes(role);

  const load = useCallback(() => {
    getStockRequest(stockRequestNo).then(setDetail).catch(toast.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stockRequestNo]);

  useEffect(load, [load]);

  function done() {
    setDialog(null);
    load();
  }

  if (!detail) return <p className="text-sm text-slate-500">Memuat...</p>;

  const open = ["REQUESTED", "PENDING_STOCK", "READY_TO_ISSUE"].includes(detail.status);
  const columns: Column<StockRequestLine & Record<string, unknown>>[] = [
    {
      key: "item_sku",
      header: "Barang",
      render: (line) => (
        <span className="font-mono-num font-semibold">
          {line.item_sku}
          {line.is_extra && <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">TAMBAHAN</span>}
        </span>
      ),
    },
    { key: "qty_required", header: "Diperlukan", className: "text-right" },
    { key: "qty_issued", header: "Dikeluarkan", className: "text-right" },
    { key: "qty_used", header: "Terpakai", className: "text-right" },
    { key: "qty_returned", header: "Kembali", className: "text-right" },
    { key: "qty_damaged", header: "Rusak", className: "text-right" },
    { key: "unit", header: "Satuan" },
  ];

  return (
    <div>
      <Link href="/stock-requests" className="text-sm text-slate-500 hover:text-slate-800">
        &larr; Permintaan Barang
      </Link>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h1 className="font-display text-2xl font-extrabold text-slate-900">{detail.stock_request_no}</h1>
        <StatusBadge status={detail.status} />
        {detail.return_pending && (
          <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800">
            return pending: laporan teknisi belum masuk
          </span>
        )}
        {detail.discrepancy && (
          <span className="rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700">
            ada selisih jumlah
          </span>
        )}
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-4 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-3 lg:grid-cols-6">
        <Info label="Tiket">{detail.ticket_code}</Info>
        <Info label="Gudang">{detail.warehouse_code}</Info>
        <Info label="Kota">{detail.city_code}</Info>
        <Info label="Teknisi">{detail.technician_employee_id ?? "belum ditugaskan"}</Info>
        <Info label="Reservasi sampai">{formatDate(detail.reserved_until)}</Info>
        <Info label="Permintaan pembelian">{detail.purchase_request_no ?? "-"}</Info>
      </dl>

      {detail.status === "PENDING_STOCK" && (
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Stok kurang. Permintaan pembelian {detail.purchase_request_no ?? "(belum ada)"} sudah dibuat; permintaan ini siap dikeluarkan
          otomatis setelah barang masuk.
        </p>
      )}
      {detail.status === "CANCELLED" && detail.cancel_reason && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">Dibatalkan: {detail.cancel_reason}</p>
      )}

      <div className="mt-6">
        <DataTable
          columns={columns}
          rows={detail.lines as (StockRequestLine & Record<string, unknown>)[]}
          rowKey={(line) => `${line.item_sku}-${line.is_extra ? "x" : "p"}`}
        />
      </div>

      {canAct && (
        <div className="mt-6 flex flex-wrap gap-2">
          {detail.status === "READY_TO_ISSUE" && <Button onClick={() => setDialog("issue")}>Keluarkan</Button>}
          {detail.status === "ISSUED" && <Button variant="secondary" onClick={() => setDialog("extra")}>Barang tambahan</Button>}
          {(detail.status === "ISSUED" || detail.status === "RETURNED") && (
            <Button variant="secondary" onClick={() => setDialog("damaged")}>Tandai rusak</Button>
          )}
          {open && <Button variant="danger" onClick={() => setDialog("cancel")}>Batalkan</Button>}
        </div>
      )}

      {dialog === "issue" && <IssueDialog request={detail} onClose={() => setDialog(null)} onDone={done} />}
      {dialog === "extra" && <ExtraDialog request={detail} onClose={() => setDialog(null)} onDone={done} />}
      {dialog === "damaged" && <DamagedDialog request={detail} onClose={() => setDialog(null)} onDone={done} />}
      {dialog === "cancel" && <CancelDialog request={detail} onClose={() => setDialog(null)} onDone={done} />}
    </div>
  );
}

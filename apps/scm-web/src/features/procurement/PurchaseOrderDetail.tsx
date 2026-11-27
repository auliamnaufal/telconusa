"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import { formatIDR, getAuth } from "@/lib/auth";
import { getPurchaseOrder } from "./api";
import { DecisionDialog, QuoteDialog, ReceiveDialog, SubmitDialog } from "./dialogs";
import {
  MIN_QUOTES,
  PROCUREMENT_ROLES,
  RECEIVING_ROLES,
  type PurchaseOrderDetail as Order,
  type PurchaseOrderLine,
} from "./types";

function formatTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("id-ID", { timeZone: "Asia/Jakarta" }) : "-";
}

export function PurchaseOrderDetail({ poNo }: { poNo: string }) {
  const toast = useToast();
  const user = getAuth().user;
  const [order, setOrder] = useState<Order | null>(null);
  const [failed, setFailed] = useState(false);
  const [dialog, setDialog] = useState<"approve" | "reject" | "receive" | "quote" | "submit" | null>(null);

  const load = useCallback(
    (signal?: AbortSignal) => {
      getPurchaseOrder(poNo, signal)
        .then((result) => {
          setOrder(result);
          setFailed(false);
        })
        .catch((error) => {
          if (error?.name !== "AbortError") {
            toast.error(error);
            setFailed(true);
          }
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [poNo],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  if (!order) {
    return <p className="text-sm text-slate-500">{failed ? "PO tidak dapat dimuat." : "Memuat..."}</p>;
  }

  const role = user?.role ?? "";
  const canDecide =
    order.status === "PENDING_APPROVAL" &&
    order.required_roles.includes(role) &&
    order.created_by !== user?.code &&
    !order.approvals.some((approval) => approval.role === role);
  const canReceive = ["APPROVED", "PARTIALLY_RECEIVED"].includes(order.status) && RECEIVING_ROLES.includes(role);

  const canPrepare = order.status === "DRAFT" && PROCUREMENT_ROLES.includes(role);
  const showQuotes = order.status === "DRAFT" || order.quotes.length > 0;

  function done() {
    setDialog(null);
    load();
  }

  const lineColumns: Column<PurchaseOrderLine>[] = [
    { key: "item_sku", header: "SKU", className: "font-mono-num font-semibold" },
    { key: "qty", header: "Dipesan" },
    { key: "qty_received", header: "Diterima" },
    { key: "unit_price", header: "Harga satuan", render: (row) => formatIDR(row.unit_price) },
    { key: "subtotal", header: "Subtotal", render: (row) => formatIDR(row.qty * row.unit_price) },
  ];

  return (
    <div>
      <Link href="/procurement" className="text-sm text-slate-500 hover:text-slate-800">
        &larr; Pengadaan
      </Link>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900">{order.po_no}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {order.vendor_name ?? order.vendor_code} ({order.vendor_code}) · PR {order.purchase_request_no ?? "-"} · dibuat oleh{" "}
            {order.created_by}, {formatTime(order.created_at)}
          </p>
          <p className="mt-2 flex items-center gap-3">
            <StatusBadge status={order.status} />
            <strong className="text-slate-900">{formatIDR(order.total_amount)}</strong>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {canDecide && (
            <>
              <Button onClick={() => setDialog("approve")}>Setujui</Button>
              <Button variant="danger" onClick={() => setDialog("reject")}>
                Tolak
              </Button>
            </>
          )}
          {canReceive && <Button onClick={() => setDialog("receive")}>Terima barang</Button>}
          {canPrepare && (
            <>
              <Button variant="secondary" onClick={() => setDialog("quote")}>
                Tambah penawaran
              </Button>
              {order.quotes.length >= MIN_QUOTES && <Button onClick={() => setDialog("submit")}>Ajukan</Button>}
            </>
          )}
        </div>
      </div>

      <h2 className="mt-8 font-display text-lg font-bold text-slate-900">Baris pesanan</h2>
      <div className="mt-3">
        <DataTable columns={lineColumns} rows={order.lines} rowKey={(row) => row.item_sku} />
      </div>

      {showQuotes && (
        <>
          <h2 className="mt-8 font-display text-lg font-bold text-slate-900">Penawaran vendor</h2>
          {order.status === "DRAFT" && (
            <p className="mt-1 text-sm text-amber-700">
              {order.quotes.length} dari {MIN_QUOTES} penawaran. PO baru bisa diajukan setelah lengkap.
            </p>
          )}
          <ul className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white text-sm">
            {order.quotes.length === 0 && <li className="px-4 py-2.5 text-slate-500">Belum ada penawaran.</li>}
            {order.quotes.map((quote) => (
              <li key={quote.vendor_code} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
                <span className="font-mono-num font-semibold">{quote.vendor_code}</span>
                <span className="text-slate-600">
                  {formatIDR(quote.unit_price)} per satuan
                  {quote.notes && <em> &ldquo;{quote.notes}&rdquo;</em>}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2 className="mt-8 font-display text-lg font-bold text-slate-900">Rantai persetujuan</h2>
      <ul className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white text-sm">
        {order.required_roles.map((required) => {
          const approval = order.approvals.find((entry) => entry.role === required);
          return (
            <li key={required} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
              <span className="font-mono-num font-semibold">{required}</span>
              {approval ? (
                <span className="flex flex-wrap items-center gap-2 text-slate-600">
                  <StatusBadge status={approval.decision} />
                  {approval.approver_id}, {formatTime(approval.at)}
                  {approval.comment && <em>&ldquo;{approval.comment}&rdquo;</em>}
                </span>
              ) : (
                <span className="text-slate-500">{order.status === "DRAFT" ? "menunggu pengajuan" : order.status === "PENDING_APPROVAL" ? "belum memutuskan" : "tidak memutuskan"}</span>
              )}
            </li>
          );
        })}
      </ul>

      <h2 className="mt-8 font-display text-lg font-bold text-slate-900">Penerimaan barang</h2>
      {order.receipts.length === 0 && <p className="mt-2 text-sm text-slate-500">Belum ada penerimaan.</p>}
      {order.receipts.map((receipt) => (
        <div key={receipt.gr_no} className="mt-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
          <p className="font-semibold text-slate-900">
            <span className="font-mono-num">{receipt.gr_no}</span> · {receipt.warehouse_code} · {receipt.received_by},{" "}
            {formatTime(receipt.received_at)}
          </p>
          <ul className="mt-2 space-y-1 text-slate-600">
            {receipt.lines.map((line) => (
              <li key={line.item_sku}>
                {line.item_sku}: {line.qty}
                {line.serial_numbers.length > 0 && <span className="font-mono-num"> ({line.serial_numbers.join(", ")})</span>}
              </li>
            ))}
          </ul>
        </div>
      ))}

      {(dialog === "approve" || dialog === "reject") && (
        <DecisionDialog order={order} action={dialog} onClose={() => setDialog(null)} onDone={done} />
      )}
      {dialog === "receive" && <ReceiveDialog order={order} onClose={() => setDialog(null)} onDone={done} />}
      {dialog === "quote" && <QuoteDialog order={order} onClose={() => setDialog(null)} onDone={done} />}
      {dialog === "submit" && <SubmitDialog order={order} onClose={() => setDialog(null)} onDone={done} />}
    </div>
  );
}

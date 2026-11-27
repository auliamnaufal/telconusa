"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/Button";
import { DataTable, type Column } from "@/components/DataTable";
import { inputClass } from "@/components/Field";
import { StatusBadge } from "@/components/StatusBadge";
import { useToast } from "@/components/Toast";
import { formatIDR, getAuth } from "@/lib/auth";
import { listPurchaseOrders, listPurchaseRequests } from "./api";
import { CreatePoDialog, CreatePoFromRequestDialog } from "./dialogs";
import {
  PO_STATUSES,
  PR_READ_ROLES,
  PR_STATUSES,
  PROCUREMENT_ROLES,
  type CreatedPurchaseOrder,
  type PurchaseOrderSummary,
  type PurchaseRequestSummary,
} from "./types";

const LIMIT = 20;

function usePagedList<T>(load: (status: string, page: number, limit: number, signal: AbortSignal) => Promise<T[]>, enabled: boolean) {
  const toast = useToast();
  const [query, setQuery] = useState({ status: "", page: 1, version: 0 });
  const [rows, setRows] = useState<T[] | null>(null);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    setRows(null);
    load(query.status, query.page, LIMIT, controller.signal)
      .then(setRows)
      .catch((error) => {
        if (error?.name !== "AbortError") {
          toast.error(error);
          setRows([]);
        }
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, enabled]);

  return {
    rows,
    status: query.status,
    page: query.page,
    setStatus: (status: string) => setQuery((q) => ({ ...q, status, page: 1 })),
    setPage: (page: number) => setQuery((q) => ({ ...q, page })),
    reload: () => setQuery((q) => ({ ...q, version: q.version + 1 })),
  };
}

type ListState = {
  rows: unknown[] | null;
  status: string;
  page: number;
  setStatus: (status: string) => void;
  setPage: (page: number) => void;
  reload: () => void;
};

function ListControls({ list, statuses, title }: { list: ListState; statuses: string[]; title: string }) {
  return (
    <div className="mt-8 flex flex-wrap items-end justify-between gap-3">
      <h2 className="font-display text-lg font-bold text-slate-900">{title}</h2>
      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
        <select className={`${inputClass} !w-auto`} aria-label={`Status ${title}`} value={list.status} onChange={(e) => list.setStatus(e.target.value)}>
          <option value="">Semua status</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
        <Button variant="secondary" onClick={list.reload}>
          Muat ulang
        </Button>
        <Button variant="secondary" disabled={list.page <= 1} onClick={() => list.setPage(list.page - 1)}>
          Sebelumnya
        </Button>
        <span>Halaman {list.page}</span>
        <Button variant="secondary" disabled={!list.rows || list.rows.length < LIMIT} onClick={() => list.setPage(list.page + 1)}>
          Berikutnya
        </Button>
      </div>
    </div>
  );
}

export function ProcurementOverview() {
  const router = useRouter();
  const role = getAuth().user?.role ?? "";
  const canCreate = PROCUREMENT_ROLES.includes(role);
  const canReadRequests = PR_READ_ROLES.includes(role);
  const orders = usePagedList<PurchaseOrderSummary>(listPurchaseOrders, true);
  const requests = usePagedList<PurchaseRequestSummary>(listPurchaseRequests, canReadRequests);
  const [creating, setCreating] = useState(false);
  const [fromRequest, setFromRequest] = useState<string | null>(null);

  function created(order: CreatedPurchaseOrder) {
    setCreating(false);
    setFromRequest(null);
    router.push(`/procurement/purchase-orders/${order.po_no}`);
  }

  const orderColumns: Column<PurchaseOrderSummary>[] = [
    { key: "po_no", header: "No. PO", className: "font-mono-num font-semibold" },
    { key: "vendor_code", header: "Vendor", className: "font-mono-num" },
    { key: "total_amount", header: "Total", render: (row) => formatIDR(row.total_amount) },
    { key: "required_roles", header: "Penyetuju dibutuhkan", render: (row) => row.required_roles.join(", ") },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  ];

  const requestColumns: Column<PurchaseRequestSummary>[] = [
    { key: "purchase_request_no", header: "No. PR", className: "font-mono-num font-semibold" },
    { key: "source", header: "Sumber" },
    { key: "stock_request_no", header: "Permintaan barang", render: (row) => row.stock_request_no ?? "-" },
    { key: "warehouse_code", header: "Gudang", className: "font-mono-num" },
    { key: "estimated_total", header: "Perkiraan", render: (row) => formatIDR(row.estimated_total) },
    {
      key: "status",
      header: "Anggaran",
      render: (row) => (
        <span className="flex flex-wrap items-center gap-2">
          <StatusBadge status={row.status} />
          {row.status === "PENDING_BUDGET" && <span className="text-xs text-amber-700">menunggu Finance</span>}
          {row.budget_remaining !== null && <span className="text-xs text-slate-500">sisa {formatIDR(row.budget_remaining)}</span>}
        </span>
      ),
    },
    {
      key: "action",
      header: "",
      render: (row) =>
        canCreate && row.status === "BUDGET_OK" ? (
          <Button variant="secondary" onClick={() => setFromRequest(row.purchase_request_no)}>
            Buat PO
          </Button>
        ) : null,
    },
  ];

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold text-slate-900">Pengadaan</h1>
          <p className="mt-1 text-sm text-slate-500">Permintaan pembelian, PO, persetujuan, dan penerimaan barang.</p>
        </div>
        {canCreate && <Button onClick={() => setCreating(true)}>Buat PO</Button>}
      </div>

      <ListControls list={orders} statuses={PO_STATUSES} title="Purchase order" />
      <div className="mt-3">
        <DataTable
          columns={orderColumns}
          rows={orders.rows}
          rowKey={(row) => row.po_no}
          empty="Tidak ada PO untuk filter ini."
          onRowClick={(row) => router.push(`/procurement/purchase-orders/${row.po_no}`)}
        />
      </div>

      {canReadRequests && (
        <>
          <ListControls list={requests} statuses={PR_STATUSES} title="Permintaan pembelian" />
          <div className="mt-3">
            <DataTable
              columns={requestColumns}
              rows={requests.rows}
              rowKey={(row) => row.purchase_request_no}
              empty="Tidak ada PR untuk filter ini."
            />
          </div>
        </>
      )}

      {creating && <CreatePoDialog onClose={() => setCreating(false)} onCreated={created} />}
      {fromRequest && <CreatePoFromRequestDialog requestNo={fromRequest} onClose={() => setFromRequest(null)} onCreated={created} />}
    </div>
  );
}

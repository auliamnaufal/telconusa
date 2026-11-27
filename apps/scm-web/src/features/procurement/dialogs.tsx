"use client";

import { useEffect, useRef, useState } from "react";
import { Field, inputClass } from "@/components/Field";
import { useToast } from "@/components/Toast";
import { ActionModal } from "@/features/stock-requests/ActionModal";
import { newIdempotencyKey } from "@/lib/api";
import { formatIDR } from "@/lib/auth";
import {
  addQuote,
  createPoFromRequest,
  createPurchaseOrder,
  decidePurchaseOrder,
  getPurchaseRequest,
  receiveGoods,
  submitPurchaseOrder,
} from "./api";
import type { CreatedPurchaseOrder, PurchaseOrderDetail, PurchaseRequestDetail } from "./types";

// Kunci idempotensi dipakai ulang bila pengguna mencoba lagi isian yang sama; isian yang diubah mendapat kunci baru.
function useSubmit() {
  const toast = useToast();
  const attempt = useRef<{ payload: string; key: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function run<T>(payload: unknown, action: (key: string) => Promise<T>, onSuccess: (result: T) => string) {
    const serialized = JSON.stringify(payload);
    if (attempt.current?.payload !== serialized) attempt.current = { payload: serialized, key: newIdempotencyKey() };
    setLoading(true);
    try {
      toast.success(onSuccess(await action(attempt.current.key)));
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  }
  return { loading, run };
}

interface CreateProps {
  onClose: () => void;
  onCreated: (order: CreatedPurchaseOrder) => void;
}

function createdMessage(order: CreatedPurchaseOrder): string {
  const next = order.status === "DRAFT" ? "lengkapi penawaran lalu ajukan" : "menunggu persetujuan";
  return `${order.po_no} dibuat (${formatIDR(order.total_amount)}), ${next}`;
}

export function CreatePoDialog({ onClose, onCreated }: CreateProps) {
  const { loading, run } = useSubmit();
  const [vendor, setVendor] = useState("");
  const [sku, setSku] = useState("");
  const [qty, setQty] = useState(1);
  const body = { vendor_code: vendor.trim().toUpperCase(), item_sku: sku.trim().toUpperCase(), qty };
  return (
    <ActionModal
      title="Buat PO"
      submitLabel="Cek anggaran dan buat PO"
      loading={loading}
      disabled={!body.vendor_code || !body.item_sku || qty < 1}
      onClose={onClose}
      onSubmit={() =>
        run(body, (key) => createPurchaseOrder(body, key), (order) => {
          onCreated(order);
          return createdMessage(order);
        })
      }
    >
      <Field label="Kode vendor" hint="Contoh: VEN-0001">
        <input className={inputClass} value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="VEN-0001" required />
      </Field>
      <Field label="SKU barang" hint="Contoh: CBL-FO, ONT-01. Harga satuan mengikuti data barang.">
        <input className={inputClass} value={sku} onChange={(e) => setSku(e.target.value)} placeholder="ONT-01" required />
      </Field>
      <Field label="Jumlah">
        <input className={inputClass} type="number" min={1} step={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} required />
      </Field>
    </ActionModal>
  );
}

export function CreatePoFromRequestDialog({ requestNo, onClose, onCreated }: CreateProps & { requestNo: string }) {
  const toast = useToast();
  const { loading, run } = useSubmit();
  const [request, setRequest] = useState<PurchaseRequestDetail | null>(null);
  const [vendor, setVendor] = useState("");
  const [prices, setPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    const controller = new AbortController();
    getPurchaseRequest(requestNo, controller.signal)
      .then((detail) => {
        setRequest(detail);
        setPrices(Object.fromEntries(detail.lines.map((line) => [line.item_sku, line.estimated_unit_cost])));
      })
      .catch((error) => {
        if (error?.name !== "AbortError") toast.error(error);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestNo]);

  const body = {
    vendor_code: vendor.trim().toUpperCase(),
    unit_prices: (request?.lines ?? []).map((line) => ({ item_sku: line.item_sku, unit_price: prices[line.item_sku] ?? 0 })),
  };
  const total = (request?.lines ?? []).reduce((sum, line) => sum + line.qty * (prices[line.item_sku] ?? 0), 0);

  return (
    <ActionModal
      title={`Buat PO dari ${requestNo}`}
      submitLabel="Buat PO"
      loading={loading}
      disabled={!request || !body.vendor_code || body.unit_prices.some((line) => line.unit_price < 1)}
      onClose={onClose}
      onSubmit={() =>
        run(body, (key) => createPoFromRequest(requestNo, body, key), (order) => {
          onCreated(order);
          return createdMessage(order);
        })
      }
    >
      <Field label="Kode vendor" hint="Contoh: VEN-0001">
        <input className={inputClass} value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="VEN-0001" required />
      </Field>
      {!request && <p className="text-sm text-slate-500">Memuat baris PR...</p>}
      {request?.lines.map((line) => (
        <Field key={line.item_sku} label={`Harga satuan ${line.item_sku} (jumlah ${line.qty})`}>
          <input
            className={inputClass}
            type="number"
            min={1}
            step={1}
            value={prices[line.item_sku] ?? 0}
            onChange={(e) => setPrices((current) => ({ ...current, [line.item_sku]: Number(e.target.value) }))}
            required
          />
        </Field>
      ))}
      {request && (
        <p className="text-sm text-slate-700">
          Total <strong>{formatIDR(total)}</strong>
          {total > request.estimated_total && (
            <span className="block text-xs text-amber-700">Melebihi perkiraan PR, anggaran akan diperiksa ulang ke Finance.</span>
          )}
        </p>
      )}
    </ActionModal>
  );
}

interface OrderProps {
  order: PurchaseOrderDetail;
  onClose: () => void;
  onDone: () => void;
}

export function DecisionDialog({ order, action, onClose, onDone }: OrderProps & { action: "approve" | "reject" }) {
  const { loading, run } = useSubmit();
  const [comment, setComment] = useState("");
  const approve = action === "approve";
  const text = comment.trim() || null;
  return (
    <ActionModal
      title={`${approve ? "Setujui" : "Tolak"} ${order.po_no}`}
      submitLabel={approve ? "Setujui PO" : "Tolak PO"}
      danger={!approve}
      loading={loading}
      onClose={onClose}
      onSubmit={() =>
        run({ action, text }, (key) => decidePurchaseOrder(order.po_no, action, text, key), () => {
          onDone();
          return `${order.po_no} ${approve ? "disetujui" : "ditolak"}`;
        })
      }
    >
      <p className="text-sm text-slate-600">
        Nilai PO <strong>{formatIDR(order.total_amount)}</strong>.
        {!approve && " Satu penolakan membuat PO berstatus REJECTED."}
      </p>
      <Field label="Komentar">
        <textarea className={inputClass} rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
      </Field>
    </ActionModal>
  );
}

export function ReceiveDialog({ order, onClose, onDone }: OrderProps) {
  const { loading, run } = useSubmit();
  const open = order.lines.filter((line) => line.qty_received < line.qty);
  const [warehouse, setWarehouse] = useState(order.warehouse_code ?? "");
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const body = {
    warehouse_code: warehouse.trim().toUpperCase(),
    lines: open
      .map((line) => ({ item_sku: line.item_sku, qty: quantities[line.item_sku] ?? line.qty - line.qty_received }))
      .filter((line) => line.qty > 0),
  };
  return (
    <ActionModal
      title={`Terima barang ${order.po_no}`}
      submitLabel="Catat penerimaan"
      loading={loading}
      disabled={!body.warehouse_code || body.lines.length === 0}
      onClose={onClose}
      onSubmit={() =>
        run(body, (key) => receiveGoods(order.po_no, body, key), (result) => {
          onDone();
          return `${result.gr_no} dicatat, PO ${result.po_status}`;
        })
      }
    >
      <Field label="Gudang penerima" hint="WH-BKS, WH-BDG, atau WH-SBY">
        <input className={inputClass} value={warehouse} onChange={(e) => setWarehouse(e.target.value)} required />
      </Field>
      {open.map((line) => (
        <Field key={line.item_sku} label={`${line.item_sku} (sisa ${line.qty - line.qty_received})`} hint="Isi 0 bila belum datang.">
          <input
            className={inputClass}
            type="number"
            min={0}
            max={line.qty - line.qty_received}
            step={1}
            value={quantities[line.item_sku] ?? line.qty - line.qty_received}
            onChange={(e) => setQuantities((current) => ({ ...current, [line.item_sku]: Number(e.target.value) }))}
          />
        </Field>
      ))}
    </ActionModal>
  );
}

export function QuoteDialog({ order, onClose, onDone }: OrderProps) {
  const { loading, run } = useSubmit();
  const [vendor, setVendor] = useState("");
  const [price, setPrice] = useState(0);
  const [notes, setNotes] = useState("");
  const body = { vendor_code: vendor.trim().toUpperCase(), unit_price: price, notes: notes.trim() || null };
  return (
    <ActionModal
      title={`Tambah penawaran ${order.po_no}`}
      submitLabel="Simpan penawaran"
      loading={loading}
      disabled={!body.vendor_code || price < 1}
      onClose={onClose}
      onSubmit={() =>
        run(body, (key) => addQuote(order.po_no, body, key), () => {
          onDone();
          return `Penawaran ${body.vendor_code} dicatat`;
        })
      }
    >
      <Field label="Kode vendor" hint="Satu penawaran per vendor. Contoh: VEN-0002">
        <input className={inputClass} value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="VEN-0002" required />
      </Field>
      <Field label="Harga satuan">
        <input className={inputClass} type="number" min={1} step={1} value={price} onChange={(e) => setPrice(Number(e.target.value))} required />
      </Field>
      <Field label="Catatan">
        <textarea className={inputClass} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </Field>
    </ActionModal>
  );
}

export function SubmitDialog({ order, onClose, onDone }: OrderProps) {
  const { loading, run } = useSubmit();
  return (
    <ActionModal
      title={`Ajukan ${order.po_no}`}
      submitLabel="Ajukan untuk persetujuan"
      loading={loading}
      onClose={onClose}
      onSubmit={() =>
        run(order.po_no, (key) => submitPurchaseOrder(order.po_no, key), () => {
          onDone();
          return `${order.po_no} diajukan, menunggu persetujuan`;
        })
      }
    >
      <p className="text-sm text-slate-600">Setelah diajukan, penawaran tidak bisa ditambah lagi.</p>
    </ActionModal>
  );
}

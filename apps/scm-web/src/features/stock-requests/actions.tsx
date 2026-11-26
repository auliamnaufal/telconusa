"use client";

import { useRef, useState } from "react";
import { Field, inputClass } from "@/components/Field";
import { useToast } from "@/components/Toast";
import { cancelStockRequest, flagDamaged, issueExtra, issueStockRequest, newIdempotencyKey } from "./api";
import { ActionModal } from "./ActionModal";
import type { StockRequestDetail } from "./types";

interface DialogProps {
  request: StockRequestDetail;
  onClose: () => void;
  onDone: () => void;
}

// Kunci idempotensi dibuat sekali per dialog dan dipakai ulang saat pengguna mencoba lagi setelah galat.
function useSubmit(onDone: () => void, message: string) {
  const toast = useToast();
  const key = useRef(newIdempotencyKey());
  const [loading, setLoading] = useState(false);

  async function run(action: (key: string) => Promise<unknown>) {
    setLoading(true);
    try {
      await action(key.current);
      toast.success(message);
      onDone();
    } catch (error) {
      toast.error(error);
    } finally {
      setLoading(false);
    }
  }
  return { loading, run };
}

export function IssueDialog({ request, onClose, onDone }: DialogProps) {
  const { loading, run } = useSubmit(onDone, `${request.stock_request_no} dikeluarkan ke teknisi`);
  const lines = request.lines.filter((line) => !line.is_extra);
  return (
    <ActionModal
      title={`Keluarkan ${request.stock_request_no}`}
      submitLabel="Keluarkan ke teknisi"
      loading={loading}
      disabled={!request.technician_employee_id}
      onClose={onClose}
      onSubmit={() => run((key) => issueStockRequest(request.stock_request_no, lines.map((l) => ({ item_sku: l.item_sku, qty: l.qty_required })), key))}
    >
      <p className="text-sm text-slate-600">
        Teknisi: <strong>{request.technician_employee_id ?? "belum ditugaskan"}</strong>
      </p>
      {!request.technician_employee_id && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Teknisi belum ditugaskan oleh CRM, jadi barang belum bisa dikeluarkan.
        </p>
      )}
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 text-sm">
        {lines.map((line) => (
          <li key={line.item_sku} className="flex justify-between px-3 py-2">
            <span className="font-mono-num">{line.item_sku}</span>
            <span>
              {line.qty_required} {line.unit}
            </span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-slate-500">Unit ONT yang sudah direservasi (urut masuk tertua) otomatis dipakai.</p>
    </ActionModal>
  );
}

export function ExtraDialog({ request, onClose, onDone }: DialogProps) {
  const { loading, run } = useSubmit(onDone, "Barang tambahan dikeluarkan");
  const [sku, setSku] = useState("");
  const [qty, setQty] = useState(1);
  return (
    <ActionModal
      title="Barang tambahan"
      submitLabel="Keluarkan tambahan"
      loading={loading}
      disabled={!sku.trim() || qty < 1}
      onClose={onClose}
      onSubmit={() => run((key) => issueExtra(request.stock_request_no, [{ item_sku: sku.trim().toUpperCase(), qty }], key))}
    >
      <Field label="SKU barang" hint="Contoh: CBL-FO, RTR-AX, ONT-01">
        <input className={inputClass} value={sku} onChange={(e) => setSku(e.target.value)} placeholder="CBL-FO" required />
      </Field>
      <Field label="Jumlah">
        <input className={inputClass} type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} required />
      </Field>
    </ActionModal>
  );
}

export function DamagedDialog({ request, onClose, onDone }: DialogProps) {
  const { loading, run } = useSubmit(onDone, "Barang rusak dicatat");
  const skus = Array.from(new Set(request.lines.map((line) => line.item_sku)));
  const [sku, setSku] = useState(skus[0] ?? "");
  const [qty, setQty] = useState(1);
  const [serial, setSerial] = useState("");
  const [notes, setNotes] = useState("");
  return (
    <ActionModal
      title="Tandai barang rusak"
      submitLabel="Tandai rusak"
      danger
      loading={loading}
      disabled={!sku || qty < 1}
      onClose={onClose}
      onSubmit={() =>
        run((key) =>
          flagDamaged(
            request.stock_request_no,
            { item_sku: sku, qty, serial_number: serial.trim() || undefined, notes: notes.trim() || undefined },
            key,
          ),
        )
      }
    >
      <Field label="Barang">
        <select className={inputClass} value={sku} onChange={(e) => setSku(e.target.value)}>
          {skus.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Jumlah rusak">
        <input className={inputClass} type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} required />
      </Field>
      <Field label="Nomor seri" hint="Wajib untuk unit ONT (satu unit per pencatatan); kosongkan untuk barang non-serial.">
        <input className={inputClass} value={serial} onChange={(e) => setSerial(e.target.value)} placeholder="SN-ONT-2026-000001" />
      </Field>
      <Field label="Catatan">
        <input className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Port LAN mati" />
      </Field>
    </ActionModal>
  );
}

export function CancelDialog({ request, onClose, onDone }: DialogProps) {
  const { loading, run } = useSubmit(onDone, `${request.stock_request_no} dibatalkan`);
  const [reason, setReason] = useState("");
  return (
    <ActionModal
      title={`Batalkan ${request.stock_request_no}`}
      submitLabel="Batalkan permintaan"
      danger
      loading={loading}
      disabled={!reason.trim()}
      onClose={onClose}
      onSubmit={() => run((key) => cancelStockRequest(request.stock_request_no, reason.trim(), key))}
    >
      <p className="text-sm text-slate-600">Reservasi stok dilepas dan tidak bisa dikembalikan. Wajib mengisi alasan.</p>
      <Field label="Alasan">
        <textarea className={inputClass} rows={3} value={reason} onChange={(e) => setReason(e.target.value)} required />
      </Field>
    </ActionModal>
  );
}

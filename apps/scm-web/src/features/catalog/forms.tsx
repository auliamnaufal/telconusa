"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/Button";
import { Field, inputClass } from "@/components/Field";
import { useToast } from "@/components/Toast";
import {
  createItem,
  createVendor,
  newIdempotencyKey,
  replacePackageKit,
  updateItem,
  updateVendor,
  type Item,
  type PackageKit,
  type Vendor,
} from "./api";
import { FormModal } from "./FormModal";

interface FormProps<T> {
  initial: T | null; // null = tambah baru
  onClose: () => void;
  onDone: () => void;
}

function useSubmit(onDone: () => void) {
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  async function run(action: () => Promise<unknown>, message: string) {
    setLoading(true);
    try {
      await action();
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

const toInt = (value: string) => (value.trim() === "" ? NaN : Number(value));

// ---------------------------------------------------------------------------- barang

export function ItemForm({ initial, onClose, onDone }: FormProps<Item>) {
  const { loading, run } = useSubmit(onDone);
  const key = useRef(newIdempotencyKey());
  const [form, setForm] = useState({
    sku: initial?.sku ?? "",
    name: initial?.name ?? "",
    unit: initial?.unit ?? "PCS",
    unit_cost: String(initial?.unit_cost ?? ""),
    reorder_point: String(initial?.reorder_point ?? 100),
    safety_stock: String(initial?.safety_stock ?? 50),
    is_serialized: initial?.is_serialized ?? false,
    specification: initial?.specification ?? "",
  });
  const set = (patch: Partial<typeof form>) => setForm((current) => ({ ...current, ...patch }));

  function submit() {
    const body = {
      name: form.name.trim(),
      unit: form.unit.trim(),
      unit_cost: toInt(form.unit_cost),
      reorder_point: toInt(form.reorder_point),
      safety_stock: toInt(form.safety_stock),
      is_serialized: form.is_serialized,
      specification: form.specification.trim() || null,
    };
    if (initial) run(() => updateItem(initial.sku, body), `Barang ${initial.sku} diperbarui`);
    else run(() => createItem({ sku: form.sku.trim().toUpperCase(), ...body }, key.current), `Barang ${form.sku.toUpperCase()} ditambahkan`);
  }

  return (
    <FormModal title={initial ? `Ubah barang ${initial.sku}` : "Tambah barang"} submitLabel="Simpan" loading={loading} onClose={onClose} onSubmit={submit}>
      {!initial && (
        <Field label="SKU" hint="Huruf besar, angka, dan tanda hubung. Contoh SPL-14">
          <input className={inputClass} required value={form.sku} onChange={(e) => set({ sku: e.target.value })} />
        </Field>
      )}
      <Field label="Nama">
        <input className={inputClass} required value={form.name} onChange={(e) => set({ name: e.target.value })} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Satuan">
          <input className={inputClass} required value={form.unit} onChange={(e) => set({ unit: e.target.value })} />
        </Field>
        <Field label="Harga satuan (Rp)">
          <input className={inputClass} required type="number" min={0} value={form.unit_cost} onChange={(e) => set({ unit_cost: e.target.value })} />
        </Field>
        <Field label="ROP per gudang">
          <input className={inputClass} required type="number" min={0} value={form.reorder_point} onChange={(e) => set({ reorder_point: e.target.value })} />
        </Field>
        <Field label="Stok pengaman">
          <input className={inputClass} required type="number" min={0} value={form.safety_stock} onChange={(e) => set({ safety_stock: e.target.value })} />
        </Field>
      </div>
      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" checked={form.is_serialized} onChange={(e) => set({ is_serialized: e.target.checked })} />
        Barang bernomor seri (dilacak per unit)
      </label>
      {initial && (
        <p className="text-xs text-slate-500">Status nomor seri tidak bisa diubah bila barang sudah punya saldo atau unit.</p>
      )}
      <Field label="Spesifikasi">
        <textarea className={inputClass} rows={2} value={form.specification} onChange={(e) => set({ specification: e.target.value })} />
      </Field>
    </FormModal>
  );
}

// ---------------------------------------------------------------------------- vendor

export function VendorForm({ initial, onClose, onDone }: FormProps<Vendor>) {
  const { loading, run } = useSubmit(onDone);
  const key = useRef(newIdempotencyKey());
  const [form, setForm] = useState({
    name: initial?.name ?? "",
    category: initial?.category ?? "",
    rating_score: String(initial?.rating_score ?? 0),
  });
  const set = (patch: Partial<typeof form>) => setForm((current) => ({ ...current, ...patch }));

  function submit() {
    const body = { name: form.name.trim(), category: form.category.trim().toUpperCase(), rating_score: Number(form.rating_score) };
    if (initial) run(() => updateVendor(initial.code, body), `Vendor ${initial.code} diperbarui`);
    else run(() => createVendor(body, key.current), "Vendor ditambahkan");
  }

  return (
    <FormModal title={initial ? `Ubah vendor ${initial.code}` : "Tambah vendor"} submitLabel="Simpan" loading={loading} onClose={onClose} onSubmit={submit}>
      <Field label="Nama">
        <input className={inputClass} required value={form.name} onChange={(e) => set({ name: e.target.value })} />
      </Field>
      <Field label="Kategori" hint="Contoh PERANGKAT_ONT, KABEL_FIBER">
        <input className={inputClass} required value={form.category} onChange={(e) => set({ category: e.target.value })} />
      </Field>
      <Field label="Rating (0–5)">
        <input className={inputClass} type="number" min={0} max={5} step={0.01} value={form.rating_score} onChange={(e) => set({ rating_score: e.target.value })} />
      </Field>
    </FormModal>
  );
}

// ---------------------------------------------------------------------------- paket

interface KitFormProps extends FormProps<PackageKit> {
  items: Item[];
}

export function KitForm({ initial, items, onClose, onDone }: KitFormProps) {
  const { loading, run } = useSubmit(onDone);
  const [serviceSku, setServiceSku] = useState(initial?.service_sku ?? "");
  const [lines, setLines] = useState(
    initial?.items.map((line) => ({ item_sku: line.item_sku, qty: String(line.qty) })) ?? [{ item_sku: items[0]?.sku ?? "", qty: "1" }],
  );

  function setLine(index: number, patch: Partial<(typeof lines)[number]>) {
    setLines((current) => current.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  }

  function submit() {
    const sku = serviceSku.trim().toUpperCase();
    run(() => replacePackageKit(sku, lines.map((line) => ({ item_sku: line.item_sku, qty: toInt(line.qty) }))), `Daftar barang ${sku} disimpan`);
  }

  return (
    <FormModal
      title={initial ? `Ubah daftar barang ${initial.service_sku}` : "Tambah daftar barang paket"}
      submitLabel="Simpan"
      loading={loading}
      onClose={onClose}
      onSubmit={submit}
    >
      {!initial && (
        <Field label="SKU paket layanan" hint="Sama dengan SKU paket di CRM, contoh MOB-PRE-50">
          <input className={inputClass} required value={serviceSku} onChange={(e) => setServiceSku(e.target.value)} />
        </Field>
      )}
      <p className="text-xs text-slate-500">Seluruh baris diganti dengan daftar di bawah. Satuan mengikuti data barang.</p>
      <div className="space-y-2">
        {lines.map((line, index) => (
          <div key={index} className="flex items-center gap-2">
            <select className={inputClass} value={line.item_sku} onChange={(e) => setLine(index, { item_sku: e.target.value })}>
              {items.map((item) => (
                <option key={item.sku} value={item.sku}>
                  {item.sku} · {item.name} ({item.unit})
                </option>
              ))}
            </select>
            <input
              className={`${inputClass} w-24`}
              type="number"
              min={1}
              required
              aria-label="Jumlah"
              value={line.qty}
              onChange={(e) => setLine(index, { qty: e.target.value })}
            />
            <Button variant="secondary" disabled={lines.length <= 1} onClick={() => setLines((current) => current.filter((_, i) => i !== index))}>
              Hapus
            </Button>
          </div>
        ))}
      </div>
      <Button variant="secondary" onClick={() => setLines((current) => [...current, { item_sku: items[0]?.sku ?? "", qty: "1" }])}>
        Tambah baris
      </Button>
    </FormModal>
  );
}

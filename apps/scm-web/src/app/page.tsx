"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SCM_API, SCM_ROLES, buildEmployeeSsoUrl, clearAuth, formatIDR, getAuth } from "@/lib/auth";

type SCMTab = "stock" | "serials" | "kits" | "procurement";

export default function SCMControlTowerPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState<SCMTab>("stock");
  const [whFilter, setWhFilter] = useState<string>("ALL");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  // New PO Form (checks budget against Finance API!)
  const [poVendor, setPoVendor] = useState("VEN-0001");
  const [poSku, setPoSku] = useState("ONT-01");
  const [poQty, setPoQty] = useState(50);

  async function loadSummary(t: string) {
    const res = await fetch(`${SCM_API}/api/v1/dashboard/summary`, {
      headers: { Authorization: `Bearer ${t}` },
      cache: "no-store",
    });
    if (res.status === 401 || res.status === 403) {
      clearAuth();
      router.replace("/login");
      return;
    }
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    const { token: t, user: u } = getAuth();
    if (!t || !u || !SCM_ROLES.includes(u.role)) {
      router.replace("/login");
      return;
    }
    setToken(t);
    setUser(u);
    loadSummary(t);
  }, []);

  async function handleCreatePO(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setMsg(null);
    const res = await fetch(`${SCM_API}/api/v1/purchase-orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ vendor_code: poVendor, item_sku: poSku, qty: poQty }),
    });
    const json = await res.json();
    if (res.ok) {
      setMsg({
        ok: true,
        text: `PO ${json.po_no} terbit senilai ${formatIDR(json.total_amount)} (Cek Anggaran Finance lolos · Sisa CC-SCM: ${formatIDR(json.budget_remaining_after_check ?? 0)})`,
      });
      loadSummary(token);
    } else {
      setMsg({ ok: false, text: json.detail || "PO ditolak oleh pengecekan anggaran Finance" });
    }
  }

  async function reconcileKit(kitCode: string) {
    if (!token) return;
    const res = await fetch(`${SCM_API}/api/v1/technician-kits/reconcile`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ kit_code: kitCode, cable_used_meters: 28 }),
    });
    if (res.ok) {
      const json = await res.json();
      setMsg({ ok: true, text: `Kit ${json.kit_code} direkonsiliasi: ${json.cable_returned_meters}m kabel kembali ke stok gudang.` });
      loadSummary(token);
    }
  }

  const inventory = (data?.inventory || []).filter((r: any) => whFilter === "ALL" || r.warehouse_code === whFilter);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Dark Industrial Telemetry Header */}
      <header className="bg-slate-950 text-white border-b border-slate-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-8 w-auto" />
            <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 font-mono-num text-[11px] font-bold text-[#FF5C6C]">
              SCM CONTROL TOWER · :3003
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-400 font-mono-num hidden sm:inline">{user?.name} ({user?.role})</span>
            <a href={buildEmployeeSsoUrl(token)} className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold">
              Portal Karyawan Saya
            </a>
            <button onClick={() => { clearAuth(); router.push("/login"); }} className="px-3 py-2 rounded-lg border border-slate-700 hover:border-red-500 cursor-pointer">
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Telemetry KPI Strip */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { label: "Total SKU Fisik", val: data?.kpis.total_skus ?? "-", accent: "text-slate-900" },
            { label: "Gudang Aktif", val: data?.kpis.total_warehouses ?? "-", accent: "text-slate-900" },
            { label: "Valuasi Persediaan", val: data ? formatIDR(data.kpis.inventory_valuation_idr) : "-", accent: "text-[#E11D2E]" },
            { label: "Kit Teknisi Aktif", val: data?.kpis.active_kits ?? "-", accent: "text-amber-600" },
            { label: "Total PO Terbit", val: data?.kpis.total_purchase_orders ?? "-", accent: "text-emerald-700" },
          ].map((k) => (
            <div key={k.label} className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{k.label}</div>
              <div className={`font-mono-num text-xl font-extrabold mt-1 ${k.accent}`}>{k.val}</div>
            </div>
          ))}
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
          {[
            { id: "stock", label: "Stok & ROP Control" },
            { id: "serials", label: "Pelacakan Serial ONT" },
            { id: "kits", label: "Kit Teknisi & Retur" },
            { id: "procurement", label: "Pengadaan (PO) & Vendor" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as SCMTab)}
              className={`px-4 py-2 rounded-lg text-xs font-bold cursor-pointer transition ${
                tab === t.id ? "bg-slate-950 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {msg && (
          <div className={`rounded-xl p-4 text-xs font-semibold border ${msg.ok ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-800"}`}>
            {msg.text}
          </div>
        )}

        {tab === "stock" && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display font-bold text-sm">Matriks Stok Multi-Gudang &amp; Indikator Reorder Point (ROP)</h2>
              <div className="flex gap-1.5">
                {["ALL", "WH-BKS", "WH-BDG", "WH-SBY"].map((wh) => (
                  <button
                    key={wh}
                    onClick={() => setWhFilter(wh)}
                    className={`px-3 py-1 rounded text-[11px] font-mono-num font-bold cursor-pointer ${
                      whFilter === wh ? "bg-[#E11D2E] text-white" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {wh}
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase">
                  <tr>
                    <th className="p-3 text-left">Gudang</th>
                    <th className="p-3 text-left">SKU &amp; Spesifikasi</th>
                    <th className="p-3 text-right">Fisik</th>
                    <th className="p-3 text-right">Reserved</th>
                    <th className="p-3 text-right">Tersedia</th>
                    <th className="p-3 text-left w-48">Level vs ROP</th>
                    <th className="p-3 text-right">Unit Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((row: any, i: number) => {
                    const ratio = Math.min(100, Math.round((row.qty_available / Math.max(1, row.reorder_point)) * 100));
                    const low = row.qty_available < row.reorder_point;
                    return (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="p-3 font-mono-num font-bold">{row.warehouse_code}</td>
                        <td className="p-3">
                          <div className="font-bold text-slate-900">{row.item_sku} · {row.item_name}</div>
                          <div className="text-[11px] text-slate-400">{row.specification}</div>
                        </td>
                        <td className="p-3 text-right font-mono-num">{row.qty_physical}</td>
                        <td className="p-3 text-right font-mono-num text-amber-600">{row.qty_reserved}</td>
                        <td className="p-3 text-right font-mono-num font-bold text-slate-900">{row.qty_available} {row.unit}</td>
                        <td className="p-3">
                          <div className="flex items-center justify-between text-[10px] font-mono-num mb-1">
                            <span className={low ? "text-red-600 font-bold" : "text-emerald-700 font-bold"}>
                              {low ? "⚠ BELOW ROP" : "AMAN"}
                            </span>
                            <span>ROP: {row.reorder_point}</span>
                          </div>
                          <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                            <div className={`h-full ${low ? "bg-[#E11D2E]" : "bg-emerald-500"}`} style={{ width: `${ratio}%` }} />
                          </div>
                        </td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(row.unit_cost)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "serials" && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">Pelacakan Nomor Seri ONT (Serialized Asset Tracker)</div>
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase">
                <tr>
                  <th className="p-3 text-left">Serial Number</th>
                  <th className="p-3 text-left">SKU</th>
                  <th className="p-3 text-left">Gudang</th>
                  <th className="p-3 text-left">Status Unit</th>
                  <th className="p-3 text-left">Teknisi / Order</th>
                </tr>
              </thead>
              <tbody>
                {(data?.serialized_units || []).map((u: any) => (
                  <tr key={u.serial_number} className="border-t border-slate-100">
                    <td className="p-3 font-mono-num font-bold">{u.serial_number}</td>
                    <td className="p-3 font-mono-num">{u.item_sku}</td>
                    <td className="p-3 font-mono-num">{u.warehouse_code}</td>
                    <td className="p-3"><span className="px-2 py-0.5 rounded bg-slate-100 font-bold">{u.status}</span></td>
                    <td className="p-3 font-mono-num text-slate-600">{u.assigned_technician_id || "-"} · {u.installed_order_no || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "kits" && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">Paket Material Teknisi &amp; Rekonsiliasi Barang Sisa</div>
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase">
                <tr>
                  <th className="p-3 text-left">Kit Code</th>
                  <th className="p-3 text-left">Work Order</th>
                  <th className="p-3 text-left">Teknisi</th>
                  <th className="p-3 text-right">Kabel Keluar</th>
                  <th className="p-3 text-right">Terpakai</th>
                  <th className="p-3 text-right">Retur ke Gudang</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {(data?.technician_kits || []).map((k: any) => (
                  <tr key={k.kit_code} className="border-t border-slate-100">
                    <td className="p-3 font-mono-num font-bold">{k.kit_code}</td>
                    <td className="p-3 font-mono-num">{k.work_order_code}</td>
                    <td className="p-3 font-mono-num">{k.technician_employee_id}</td>
                    <td className="p-3 text-right font-mono-num">{k.cable_issued_meters}m</td>
                    <td className="p-3 text-right font-mono-num">{k.cable_used_meters}m</td>
                    <td className="p-3 text-right font-mono-num font-bold text-emerald-700">{k.cable_returned_meters}m</td>
                    <td className="p-3"><span className="px-2 py-0.5 rounded bg-slate-100 font-bold">{k.status}</span></td>
                    <td className="p-3 text-right">
                      <button onClick={() => reconcileKit(k.kit_code)} className="px-2.5 py-1 rounded bg-slate-900 text-white font-bold cursor-pointer">
                        Rekonsiliasi Retur
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "procurement" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-5 space-y-4">
              <h2 className="font-display font-bold text-sm">Buat Purchase Order (Otomatis Cek Anggaran Finance)</h2>
              <form onSubmit={handleCreatePO} className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Vendor</label>
                  <select value={poVendor} onChange={(e) => setPoVendor(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs">
                    {(data?.vendors || []).map((v: any) => (
                      <option key={v.code} value={v.code}>{v.code} — {v.name} (★ {v.rating_score})</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Barang SKU</label>
                    <select value={poSku} onChange={(e) => setPoSku(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs">
                      <option value="ONT-01">ONT-01 (Rp350.000)</option>
                      <option value="RTR-AX">RTR-AX (Rp500.000)</option>
                      <option value="CBL-FO">CBL-FO (Rp4.000/m)</option>
                      <option value="SIM-01">SIM-01 (Rp5.000)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Jumlah (Qty)</label>
                    <input type="number" min={1} value={poQty} onChange={(e) => setPoQty(Number(e.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                  </div>
                </div>
                <button type="submit" className="w-full py-2.5 rounded-lg bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold cursor-pointer">
                  Cek Anggaran Finance &amp; Terbitkan PO
                </button>
              </form>
            </div>

            <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">Daftar Purchase Orders &amp; Vendor Scorecard</div>
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase">
                  <tr>
                    <th className="p-3 text-left">PO No.</th>
                    <th className="p-3 text-left">Vendor</th>
                    <th className="p-3 text-left">SKU</th>
                    <th className="p-3 text-right">Qty</th>
                    <th className="p-3 text-right">Total</th>
                    <th className="p-3 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.purchase_orders || []).map((p: any) => (
                    <tr key={p.po_no} className="border-t border-slate-100">
                      <td className="p-3 font-mono-num font-bold">{p.po_no}</td>
                      <td className="p-3">{p.vendor_name}</td>
                      <td className="p-3 font-mono-num">{p.item_sku}</td>
                      <td className="p-3 text-right font-mono-num">{p.qty}</td>
                      <td className="p-3 text-right font-mono-num font-bold">{formatIDR(p.total_amount)}</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold">{p.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

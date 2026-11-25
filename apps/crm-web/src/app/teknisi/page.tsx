"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CRM_API, CRM_STAFF_ROLES, SCM_API, buildEmployeeSsoUrl, clearAuth, getAuth } from "@/lib/auth";

export default function TechnicianDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [wos, setWos] = useState<any[]>([]);
  const [kitSpec, setKitSpec] = useState<any[]>([]);
  const [formByWo, setFormByWo] = useState<Record<string, any>>({});
  const [msg, setMsg] = useState<string | null>(null);

  async function load(t: string) {
    const res = await fetch(`${CRM_API}/api/v1/dashboard/summary`, {
      headers: { Authorization: `Bearer ${t}` },
      cache: "no-store",
    });
    if (res.status === 401 || res.status === 403) {
      clearAuth();
      router.replace("/login");
      return;
    }
    if (res.ok) {
      const json = await res.json();
      setWos(json.work_orders || []);
    }
    fetch(`${SCM_API}/api/v1/items/requirements?sku=HOME-50`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setKitSpec(d.required_kit || []))
      .catch(() => {});
  }

  useEffect(() => {
    const { token: t, user: u } = getAuth();
    if (!t || !u || !CRM_STAFF_ROLES.includes(u.role)) {
      router.replace("/login");
      return;
    }
    setToken(t);
    setUser(u);
    load(t);
  }, []);

  async function completeWorkOrder(woId: string) {
    if (!token) return;
    const f = formByWo[woId] || {
      ont_serial_number: "SN-ONT-2026-000002",
      cable_used_meters: 30,
      signal_dbm: -18.5,
      speedtest_mbps: 53.2,
      site_condition_notes: "Tiang ODP depan rumah, kabel terpasang rapi.",
    };
    const res = await fetch(`${CRM_API}/api/v1/work-orders/${woId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ installation_status: "COMPLETED", ...f }),
    });
    if (res.ok) {
      setMsg("Work order selesai! Data lokasi rumah tersimpan & rekonsiliasi sisa kabel dikirim ke SCM.");
      load(token);
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="bg-slate-950 border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/teknisi">
              <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-8 w-auto" />
            </Link>
            <span className="px-2.5 py-0.5 rounded-lg bg-[#E11D2E] text-[11px] font-bold">
              CRM Internal Portal · :3001 · FIELD TECHNICIAN DISPATCH
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-300 font-semibold">{user?.name} ({user?.code})</span>
            <a href={buildEmployeeSsoUrl(token)} className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold">
              Portal Karyawan Saya (ESS)
            </a>
            <button onClick={() => { clearAuth(); router.push("/login"); }} className="px-3 py-2 rounded-xl border border-slate-700 cursor-pointer">
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {msg && <div className="rounded-xl bg-emerald-950 border border-emerald-700 p-4 text-xs text-emerald-200">{msg}</div>}

        <div className="rounded-2xl bg-slate-800/80 border border-slate-700 p-5">
          <div className="font-display font-bold text-sm text-[#FF6B7A] mb-2">
            Checklist Paket Material &amp; Spesifikasi dari SCM (Per Instalasi Rumah)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {kitSpec.map((item) => (
              <div key={item.item_sku} className="rounded-xl bg-slate-900 border border-slate-700 p-3 text-xs">
                <div className="font-bold text-white">{item.item_sku} · {item.name} ({item.qty} {item.unit})</div>
                <div className="text-slate-400 mt-1">{item.specification}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {wos.map((w) => {
            const f = formByWo[w.id] || {
              ont_serial_number: w.ont_serial_number || "SN-ONT-2026-000002",
              cable_used_meters: w.cable_used_meters || 30,
              signal_dbm: w.signal_dbm || -18.5,
              speedtest_mbps: w.speedtest_mbps || 53.0,
              site_condition_notes: w.site_condition_notes || "Kondisi instalasi aman.",
            };
            return (
              <div key={w.id} className="rounded-2xl bg-white text-slate-900 p-6 shadow-md space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-mono-num font-extrabold text-base">{w.work_order_code} — {w.customer_name} ({w.sku})</div>
                    <div className="text-xs text-slate-600 mt-0.5">📍 {w.install_address} ({w.city_code})</div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${w.installation_status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                    {w.installation_status}
                  </span>
                </div>

                {w.installation_status !== "COMPLETED" ? (
                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-3 border-t border-slate-100">
                    <input value={f.ont_serial_number} onChange={(e) => setFormByWo({ ...formByWo, [w.id]: { ...f, ont_serial_number: e.target.value } })} placeholder="SN ONT" className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                    <input type="number" value={f.cable_used_meters} onChange={(e) => setFormByWo({ ...formByWo, [w.id]: { ...f, cable_used_meters: Number(e.target.value) } })} placeholder="Kabel (m)" className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                    <input type="number" step="0.1" value={f.speedtest_mbps} onChange={(e) => setFormByWo({ ...formByWo, [w.id]: { ...f, speedtest_mbps: Number(e.target.value) } })} placeholder="Speed Mbps" className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                    <input value={f.site_condition_notes} onChange={(e) => setFormByWo({ ...formByWo, [w.id]: { ...f, site_condition_notes: e.target.value } })} placeholder="Kondisi Rumah..." className="rounded-lg border border-slate-300 px-3 py-2 text-xs" />
                    <button onClick={() => completeWorkOrder(w.id)} className="rounded-lg bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold py-2 cursor-pointer">
                      ✓ Selesaikan &amp; Retur Sisa
                    </button>
                  </div>
                ) : (
                  <div className="text-xs text-slate-600 bg-slate-50 rounded-xl p-3 font-mono-num">
                    SN: {w.ont_serial_number} · Kabel Terpakai: {w.cable_used_meters}m · Speedtest: {w.speedtest_mbps} Mbps · Catatan: {w.site_condition_notes}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}

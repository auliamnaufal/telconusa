"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CRM_API, CRM_MANAGER_ROLES, HRM_API, buildEmployeeSsoUrl, clearAuth, formatIDR, getAuth } from "@/lib/auth";

export default function CRMManagerDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [techs, setTechs] = useState<any[]>([]);
  const [orderFilter, setOrderFilter] = useState<string>("ALL");
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
    if (res.ok) setData(await res.json());
    fetch(`${HRM_API}/api/v1/employees/available?role=TECHNICIAN`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setTechs)
      .catch(() => {});
  }

  useEffect(() => {
    const { token: t, user: u } = getAuth();
    if (!t || !u || !CRM_MANAGER_ROLES.includes(u.role)) {
      router.replace("/login");
      return;
    }
    setToken(t);
    setUser(u);
    load(t);
  }, []);

  async function assignTech(woId: string, techCode: string) {
    if (!token || !techCode) return;
    const res = await fetch(`${CRM_API}/api/v1/work-orders/${woId}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ technician_employee_id: techCode }),
    });
    if (res.ok) {
      setMsg(`Teknisi ${techCode} berhasil ditugaskan & notifikasi dikirim!`);
      load(token);
    }
  }

  const orders = (data?.orders || []).filter((o: any) => orderFilter === "ALL" || o.status === orderFilter);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link href="/manager">
              <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-9 w-auto" />
            </Link>
            <span className="px-2.5 py-1 rounded-lg bg-rose-50 text-[#BE123C] text-xs font-bold">
              CRM Internal Portal · :3001 (Manajer · CS · Marketing)
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="font-semibold text-slate-600">{user?.name} ({user?.role})</span>
            <Link href="/teknisi" className="px-3 py-2 rounded-xl border border-slate-200 font-semibold hover:border-[#E11D2E]">
              Dispatch Teknisi
            </Link>
            <a href={buildEmployeeSsoUrl(token)} className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold">
              Portal Karyawan Saya
            </a>
            <button onClick={() => { clearAuth(); router.push("/login"); }} className="px-3 py-2 rounded-xl border border-slate-200 font-semibold cursor-pointer">
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {msg && <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800">{msg}</div>}

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { label: "Total Pelanggan", val: data?.kpis.total_customers ?? "-" },
            { label: "Langganan Aktif", val: data?.kpis.active_subscriptions ?? "-" },
            { label: "Work Order Aktif", val: data?.kpis.pending_work_orders ?? "-" },
            { label: "Tiket SLA Terbuka", val: data?.kpis.open_tickets ?? "-" },
            { label: "Rata-rata Rating Teknisi", val: data ? `${data.kpis.avg_technician_rating} / 5 ★` : "-" },
          ].map((k) => (
            <div key={k.label} className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="text-xs text-slate-500">{k.label}</div>
              <div className="font-mono-num text-2xl font-extrabold mt-1">{k.val}</div>
            </div>
          ))}
        </div>

        {/* Order Pipeline */}
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display font-bold text-sm">Pipeline Order &amp; Campaign Referral</h2>
            <div className="flex flex-wrap gap-1.5">
              {["ALL", "AWAITING_PAYMENT", "PAID", "ON_HOLD", "COMPLETED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setOrderFilter(st)}
                  className={`px-3 py-1 rounded-lg text-[11px] font-bold cursor-pointer ${
                    orderFilter === st ? "bg-[#E11D2E] text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {st === "ON_HOLD" ? "PENDING STOK" : st}
                </button>
              ))}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="p-3 text-left">No. Order</th>
                  <th className="p-3 text-left">Pelanggan</th>
                  <th className="p-3 text-left">Alamat Pemasangan</th>
                  <th className="p-3 text-left">SKU</th>
                  <th className="p-3 text-left">Kode Referral</th>
                  <th className="p-3 text-right">Subtotal</th>
                  <th className="p-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o: any) => (
                  <tr key={o.order_no} className="border-t border-slate-100">
                    <td className="p-3 font-mono-num font-bold">{o.order_no}</td>
                    <td className="p-3">{o.customer_name}</td>
                    <td className="p-3 text-xs text-slate-600">{o.install_address} ({o.city_code})</td>
                    <td className="p-3 font-mono-num">{o.sku}</td>
                    <td className="p-3 font-mono-num text-[#E11D2E] font-bold">{o.referral_code || "-"}</td>
                    <td className="p-3 text-right font-mono-num">{formatIDR(o.subtotal)}</td>
                    <td className="p-3"><span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold">{o.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Work Order Dispatch */}
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-display font-bold text-sm">Penugasan Teknisi (Live Ketersediaan dari HRM)</h2>
            <span className="text-xs text-emerald-700 font-semibold">{techs.length} Teknisi Tersedia</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500">
                <tr>
                  <th className="p-3 text-left">Work Order</th>
                  <th className="p-3 text-left">Pelanggan &amp; Lokasi</th>
                  <th className="p-3 text-left">Teknisi Aktif</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-right">Tugaskan Teknisi (HRM)</th>
                </tr>
              </thead>
              <tbody>
                {(data?.work_orders || []).map((w: any) => (
                  <tr key={w.id} className="border-t border-slate-100">
                    <td className="p-3 font-mono-num font-bold">{w.work_order_code}</td>
                    <td className="p-3 text-xs">{w.customer_name} — {w.install_address}</td>
                    <td className="p-3 font-mono-num font-semibold">{w.technician_employee_id || "Belum ada"}</td>
                    <td className="p-3"><span className="px-2 py-0.5 rounded bg-slate-100 text-xs font-bold">{w.installation_status}</span></td>
                    <td className="p-3 text-right">
                      <select
                        defaultValue=""
                        onChange={(e) => assignTech(w.id, e.target.value)}
                        className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs"
                      >
                        <option value="" disabled>Pilih Teknisi Tersedia...</option>
                        {techs.map((t) => (
                          <option key={t.employee_code} value={t.employee_code}>
                            {t.employee_code} · {t.full_name} ({t.city_code})
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tickets SLA & Campaigns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-100 font-display font-bold text-sm">
              Tiket Keluhan &amp; Layanan CS (Dari Landing &amp; Portal)
            </div>
            <div className="divide-y divide-slate-100">
              {(data?.tickets || []).map((t: any) => (
                <div key={t.ticket_code} className="p-4 text-xs flex justify-between items-start gap-3">
                  <div>
                    <div className="font-mono-num font-bold">
                      {t.ticket_code} · {t.customer_name}{" "}
                      <span className="font-normal text-slate-400">({t.customer_email || t.customer_code})</span>
                    </div>
                    <div className="font-semibold text-slate-800 mt-0.5">{t.subject}</div>
                    {t.description && <div className="text-slate-500 mt-0.5">{t.description}</div>}
                  </div>
                  <span className="px-2.5 py-1 rounded bg-rose-50 text-[#BE123C] font-bold shrink-0">
                    {t.priority} · {t.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-100 font-display font-bold text-sm">Campaign Marketing Aktif</div>
            <div className="p-4 space-y-3">
              {(data?.campaigns || []).map((c: any) => (
                <div key={c.campaign_code} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-mono-num font-bold text-[#E11D2E]">{c.campaign_code}</div>
                    <div className="font-semibold text-slate-900 mt-0.5">{c.name}</div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">{c.channel}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

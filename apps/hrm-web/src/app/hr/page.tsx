"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { HR_ADMIN_ROLES, HRM_API, clearAuth, formatIDR, getAuth } from "@/lib/auth";

type HRTab = "directory" | "referrals" | "performance" | "payroll" | "recruitment";

export default function InternalHRWorkspacePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [tab, setTab] = useState<HRTab>("directory");
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);

  // Forms
  const [newRefEmp, setNewRefEmp] = useState("EMP-0010");
  const [newRefCustom, setNewRefCustom] = useState("");
  const [newReqDept, setNewReqDept] = useState("DEP-OPS");
  const [newReqTitle, setNewReqTitle] = useState("");
  const [newReqCount, setNewReqCount] = useState(1);

  async function loadSummary(t: string) {
    const res = await fetch(`${HRM_API}/api/v1/dashboard/summary`, {
      headers: { Authorization: `Bearer ${t}` },
      cache: "no-store",
    });
    if (res.status === 401) {
      clearAuth();
      router.replace("/login");
      return;
    }
    if (res.status === 403) {
      setForbidden(true);
      return;
    }
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    const { token: t, user: u } = getAuth();
    if (!t || !u) {
      router.replace("/login");
      return;
    }
    setUser(u);
    setToken(t);
    if (!HR_ADMIN_ROLES.includes(u.role)) {
      setForbidden(true);
      return;
    }
    loadSummary(t);
  }, []);

  async function toggleAvail(empCode: string) {
    if (!token) return;
    const res = await fetch(`${HRM_API}/api/v1/employees/${empCode}/availability`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const json = await res.json();
      setMsg(`Status ketersediaan ${json.employee_code} diubah menjadi ${json.is_available ? "TERSEDIA" : "CUTI/OFF"} (langsung sinkron ke dispatch CRM).`);
      loadSummary(token);
    }
  }

  async function createReferral(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    const res = await fetch(`${HRM_API}/api/v1/referrals`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ employee_code: newRefEmp, custom_code: newRefCustom.trim() || null }),
    });
    const json = await res.json();
    if (res.ok) {
      setMsg(`Kode referral ${json.code} berhasil dibuat untuk ${json.employee_code}!`);
      setNewRefCustom("");
      loadSummary(token);
    } else {
      setMsg(json.detail || "Gagal membuat kode referral");
    }
  }

  async function approvePayroll(period: string) {
    if (!token) return;
    const res = await fetch(`${HRM_API}/api/v1/payroll-runs/${period}/approve-hr`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setMsg(`Payroll ${period} disetujui HR → event payroll.approved dikirim ke Finance!`);
      loadSummary(token);
    }
  }

  async function createRequisition(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    const res = await fetch(`${HRM_API}/api/v1/requisitions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ department_code: newReqDept, position_title: newReqTitle, headcount: newReqCount }),
    });
    if (res.ok) {
      const json = await res.json();
      setMsg(`Pengajuan tenaga kerja ${json.req_code} berhasil dibuka.`);
      setNewReqTitle("");
      loadSummary(token);
    }
  }

  if (forbidden) {
    return (
      <div className="min-h-screen bg-rose-50/40 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-3xl border border-rose-200 p-8 text-center shadow-lg">
          <div className="text-3xl mb-3">🔒</div>
          <h1 className="font-display text-xl font-extrabold text-slate-900">403 — Akses Khusus Tim HR</h1>
          <p className="text-xs text-slate-600 mt-2 mb-6">
            Akun Anda (<strong>{user?.name} · {user?.role}</strong>) tidak memiliki izin untuk membuka data admin HR. Silakan gunakan <strong>Portal Karyawan Saya</strong> untuk absensi, cuti, dan slip gaji pribadi.
          </p>
          <Link href="/karyawan" className="inline-block px-6 py-3 rounded-xl bg-[#E11D2E] text-white text-xs font-bold">
            Masuk ke Portal Karyawan Saya →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-[#FFF9FA] text-slate-900">
      {/* Warm People-Centric Sidebar */}
      <aside className="w-64 shrink-0 bg-white border-r border-rose-100 flex flex-col">
        <div className="p-5 border-b border-rose-100">
          <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-8 w-auto" />
          <div className="mt-2 inline-block px-2.5 py-0.5 rounded-full bg-rose-50 text-[#BE123C] text-[10px] font-extrabold uppercase tracking-wider">
            Internal HR Workspace
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {[
            { id: "directory", label: "Direktori & Ketersediaan" },
            { id: "referrals", label: "Kode Referral Marketing" },
            { id: "performance", label: "Kinerja & Rating Teknisi" },
            { id: "payroll", label: "Konsol Payroll Bulanan" },
            { id: "recruitment", label: "Rekrutmen & Cuti" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id as HRTab)}
              className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                tab === item.id ? "bg-[#E11D2E] text-white shadow-sm" : "text-slate-600 hover:bg-rose-50 hover:text-[#BE123C]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-rose-100 space-y-2">
          <Link href="/karyawan" className="block w-full text-center py-2.5 rounded-xl bg-rose-50 text-[#BE123C] text-xs font-bold hover:bg-rose-100">
            👤 Portal Karyawan Saya
          </Link>
          <button onClick={() => { clearAuth(); router.push("/login"); }} className="block w-full py-2 text-xs text-slate-500 hover:text-slate-800 cursor-pointer">
            Keluar Akun
          </button>
        </div>
      </aside>

      {/* Main HR Content */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="bg-white border-b border-rose-100 px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="font-display text-xl font-extrabold text-slate-900">Human Resource Management (HRM)</h1>
            <p className="text-xs text-slate-500">Login sebagai: <strong>{user?.name}</strong> ({user?.role})</p>
          </div>
          <span className="font-mono-num text-xs px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 font-bold">
            ● HRM API :8002
          </span>
        </header>

        <main className="p-8 max-w-6xl w-full mx-auto space-y-6">
          {msg && <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800">{msg}</div>}

          {/* KPI Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { label: "Total Karyawan", val: data?.kpis.total_employees ?? "-" },
              { label: "Teknisi Tersedia", val: data?.kpis.available_technicians ?? "-" },
              { label: "Kode Referral Aktif", val: data?.kpis.active_referral_codes ?? "-" },
              { label: "Lowongan Terbuka", val: data?.kpis.open_requisitions ?? "-" },
              { label: "Biaya Payroll Periode", val: data ? formatIDR(data.kpis.latest_payroll_cost) : "-" },
            ].map((k) => (
              <div key={k.label} className="bg-white rounded-2xl border border-rose-100 p-4 shadow-xs">
                <div className="text-xs text-slate-500">{k.label}</div>
                <div className="font-mono-num text-xl font-extrabold text-slate-900 mt-1">{k.val}</div>
              </div>
            ))}
          </div>

          {tab === "directory" && (
            <div className="bg-white rounded-2xl border border-rose-100 overflow-hidden shadow-xs">
              <div className="px-5 py-4 border-b border-rose-50 font-display font-bold text-sm">
                Direktori Karyawan &amp; Ketersediaan Penugasan CRM
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-rose-50/60 text-xs text-slate-600">
                    <tr>
                      <th className="p-3 text-left">NIP</th>
                      <th className="p-3 text-left">Nama Lengkap</th>
                      <th className="p-3 text-left">Role</th>
                      <th className="p-3 text-left">Kota / Shift</th>
                      <th className="p-3 text-right">Skor KPI</th>
                      <th className="p-3 text-left">Status Siap</th>
                      <th className="p-3 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.employees || []).map((e: any) => (
                      <tr key={e.employee_code} className="border-t border-rose-50">
                        <td className="p-3 font-mono-num font-bold">{e.employee_code}</td>
                        <td className="p-3 font-semibold">{e.full_name}<div className="text-[11px] text-slate-400">{e.email}</div></td>
                        <td className="p-3 text-xs font-mono-num">{e.role}</td>
                        <td className="p-3 text-xs">{e.city_code} · {e.shift_name}</td>
                        <td className="p-3 text-right font-mono-num font-bold">{e.kpi_score}</td>
                        <td className="p-3">
                          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${e.is_available ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                            {e.is_available ? "TERSEDIA" : "CUTI / OFF"}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button onClick={() => toggleAvail(e.employee_code)} className="px-3 py-1 rounded-lg border border-rose-200 hover:bg-rose-50 text-[11px] font-bold text-[#BE123C] cursor-pointer">
                            Toggle Status
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "referrals" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-4 bg-white rounded-2xl border border-rose-100 p-5">
                <h2 className="font-display font-bold text-sm mb-3">Generate Kode Referral Marketing</h2>
                <form onSubmit={createReferral} className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Pilih Karyawan</label>
                    <select value={newRefEmp} onChange={(e) => setNewRefEmp(e.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs">
                      {(data?.employees || []).map((e: any) => (
                        <option key={e.employee_code} value={e.employee_code}>{e.employee_code} — {e.full_name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Custom Kode (Opsional)</label>
                    <input value={newRefCustom} onChange={(e) => setNewRefCustom(e.target.value)} placeholder="Mis. NUSA-DEWI" className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                  </div>
                  <button type="submit" className="w-full py-2.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold cursor-pointer">
                    + Terbitkan Kode Referral
                  </button>
                </form>
              </div>

              <div className="lg:col-span-8 bg-white rounded-2xl border border-rose-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-rose-50 font-display font-bold text-sm">
                  Leaderboard Referral (Insentif 10% Bulan Pertama + 10 Poin KPI)
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-rose-50/60 text-xs text-slate-600">
                    <tr>
                      <th className="p-3 text-left">Kode</th>
                      <th className="p-3 text-left">Staf Marketing</th>
                      <th className="p-3 text-right">Pemakaian</th>
                      <th className="p-3 text-right">Total Insentif</th>
                      <th className="p-3 text-right">Poin KPI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.referrals || []).map((r: any) => (
                      <tr key={r.code} className="border-t border-rose-50">
                        <td className="p-3 font-mono-num font-bold text-[#E11D2E]">{r.code}</td>
                        <td className="p-3">{r.employee_name} ({r.employee_code})</td>
                        <td className="p-3 text-right font-mono-num">{r.total_uses}x</td>
                        <td className="p-3 text-right font-mono-num font-bold">{formatIDR(r.total_incentive || 0)}</td>
                        <td className="p-3 text-right font-mono-num font-bold text-emerald-700">+{r.total_kpi_points}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "performance" && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-rose-100 p-5">
                <div className="font-display font-bold text-sm mb-2">Formula Penilaian Kinerja Kuartalan HRM</div>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="rounded-xl bg-rose-50 p-3"><strong>60% KPI Jabatan</strong><div className="text-slate-600 mt-0.5">Teknisi: 40% Rating Pelanggan CRM + 60% Ketepatan Instalasi</div></div>
                  <div className="rounded-xl bg-slate-50 p-3"><strong>25% Perilaku</strong><div className="text-slate-600 mt-0.5">Evaluasi atasan langsung &amp; kedisiplinan</div></div>
                  <div className="rounded-xl bg-slate-50 p-3"><strong>15% Kehadiran</strong><div className="text-slate-600 mt-0.5">Absensi tepat waktu &amp; kepatuhan shift GPS</div></div>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-rose-100 p-5 space-y-3">
                <div className="font-display font-bold text-sm">Log Rating Pelanggan CRM untuk Teknisi</div>
                {(data?.technician_ratings || []).map((rt: any) => (
                  <div key={rt.work_order_code} className="p-4 rounded-xl bg-rose-50/40 border border-rose-100 flex items-center justify-between gap-4 text-xs">
                    <div>
                      <div className="font-bold">{rt.technician_name} ({rt.technician_employee_id}) · {rt.work_order_code}</div>
                      <p className="text-slate-600 mt-1">{rt.rating_comment}</p>
                    </div>
                    <div className="text-amber-500 text-base font-bold shrink-0">{"★".repeat(rt.rating_score)} ({rt.rating_score}/5)</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "payroll" && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-rose-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-rose-50 flex items-center justify-between">
                  <span className="font-display font-bold text-sm">Kalender Payroll Bulanan (Cut-off Tgl 20 · Bayar Tgl 28)</span>
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-rose-50/60 text-xs text-slate-600">
                    <tr>
                      <th className="p-3 text-left">Periode</th>
                      <th className="p-3 text-right">Pendapatan Bruto</th>
                      <th className="p-3 text-right">BPJS Perusahaan</th>
                      <th className="p-3 text-right">PPh 21</th>
                      <th className="p-3 text-right">Total Biaya Perusahaan</th>
                      <th className="p-3 text-left">Status</th>
                      <th className="p-3 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.payroll_runs || []).map((p: any) => (
                      <tr key={p.payroll_period} className="border-t border-rose-50">
                        <td className="p-3 font-mono-num font-bold">{p.payroll_period}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(p.total_gross)}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(p.total_bpjs_company)}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(p.total_pph21)}</td>
                        <td className="p-3 text-right font-mono-num font-bold">{formatIDR(p.total_company_cost)}</td>
                        <td className="p-3"><span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-xs font-bold">{p.status}</span></td>
                        <td className="p-3 text-right">
                          <button onClick={() => approvePayroll(p.payroll_period)} className="px-3.5 py-1.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold cursor-pointer">
                            Approve HR → Kirim Finance
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="bg-white rounded-2xl border border-rose-100 overflow-x-auto">
                <div className="px-5 py-3.5 border-b border-rose-50 font-display font-bold text-sm">Rincian Komponen Payroll Karyawan</div>
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="p-3 text-left">Karyawan</th>
                      <th className="p-3 text-right">Pokok + Tunjangan</th>
                      <th className="p-3 text-right">Transport</th>
                      <th className="p-3 text-right">Lembur</th>
                      <th className="p-3 text-right">Bruto</th>
                      <th className="p-3 text-right">BPJS + PPh 21</th>
                      <th className="p-3 text-right">Gaji Bersih</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.payroll_items || []).map((pi: any) => (
                      <tr key={pi.employee_code} className="border-t border-slate-100">
                        <td className="p-3 font-bold">{pi.employee_name} ({pi.employee_code})</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(pi.base_salary + pi.allowance)}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(pi.transport_meal)}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(pi.overtime_pay)}</td>
                        <td className="p-3 text-right font-mono-num font-bold">{formatIDR(pi.gross_salary)}</td>
                        <td className="p-3 text-right font-mono-num text-red-600">-{formatIDR(pi.bpjs_employee + pi.pph21_amount)}</td>
                        <td className="p-3 text-right font-mono-num font-extrabold text-emerald-700">{formatIDR(pi.net_salary)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "recruitment" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-5 bg-white rounded-2xl border border-rose-100 p-5">
                <h2 className="font-display font-bold text-sm mb-3">Pengajuan Kebutuhan Tenaga Kerja (Dari Divisi)</h2>
                <form onSubmit={createRequisition} className="space-y-3">
                  <select value={newReqDept} onChange={(e) => setNewReqDept(e.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs">
                    <option value="DEP-OPS">DEP-OPS — Operasional &amp; Teknisi</option>
                    <option value="DEP-SALES">DEP-SALES — Sales &amp; Marketing</option>
                    <option value="DEP-SCM">DEP-SCM — Gudang &amp; Pengadaan</option>
                    <option value="DEP-FIN">DEP-FIN — Keuangan</option>
                  </select>
                  <input required value={newReqTitle} onChange={(e) => setNewReqTitle(e.target.value)} placeholder="Posisi yang dibutuhkan..." className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs" />
                  <input type="number" min={1} value={newReqCount} onChange={(e) => setNewReqCount(Number(e.target.value))} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                  <button type="submit" className="w-full py-2.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold cursor-pointer">+ Ajukan Formasi</button>
                </form>
              </div>
              <div className="lg:col-span-7 bg-white rounded-2xl border border-rose-100 p-5 space-y-3">
                <h2 className="font-display font-bold text-sm">Daftar Rekrutmen &amp; Pengajuan Cuti</h2>
                {(data?.requisitions || []).map((rq: any) => (
                  <div key={rq.req_code} className="p-3 rounded-xl bg-rose-50/40 border border-rose-100 flex justify-between text-xs">
                    <div><strong>{rq.req_code}</strong> · {rq.position_title} ({rq.department_code})</div>
                    <span className="font-bold text-[#BE123C]">{rq.headcount} org · {rq.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

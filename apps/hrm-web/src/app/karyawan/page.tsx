"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { HRM_API, clearAuth, consumeSsoHash, formatIDR, getDivisionPortalLink } from "@/lib/auth";

export default function EmployeeSelfServicePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [gps, setGps] = useState("-6.8842,107.6138 (Lokasi Kerja)");
  const [leaveForm, setLeaveForm] = useState({ leave_type: "ANNUAL", start_date: "2026-12-01", end_date: "2026-12-02", reason: "" });

  async function loadSelfService(t: string, empCode: string) {
    const res = await fetch(`${HRM_API}/api/v1/employees/${empCode}/self-service`, {
      headers: { Authorization: `Bearer ${t}` },
      cache: "no-store",
    });
    if (res.status === 401) {
      clearAuth();
      router.replace("/login");
      return;
    }
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    consumeSsoHash().then(({ token: t, user: u }) => {
      if (!t || !u) {
        router.replace("/login");
        return;
      }
      setToken(t);
      setUser(u);
      loadSelfService(t, u.code);
    });
  }, []);

  async function handleCheckIn() {
    if (!token || !user) return;
    const res = await fetch(`${HRM_API}/api/v1/attendance/check-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ gps_location: gps }),
    });
    if (res.ok) {
      const json = await res.json();
      setMsg(`Absen masuk tercatat pada ${json.check_in_time} WIB (${json.gps_location}).`);
      loadSelfService(token, user.code);
    }
  }

  async function handleLeave(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !user) return;
    const res = await fetch(`${HRM_API}/api/v1/leaves`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(leaveForm),
    });
    if (res.ok) {
      setMsg("Pengajuan cuti berhasil dikirim ke atasan & HRM.");
      setLeaveForm({ ...leaveForm, reason: "" });
      loadSelfService(token, user.code);
    }
  }

  const divLink = getDivisionPortalLink(user?.role);

  return (
    <div className="min-h-screen bg-[#FFF9FA] text-slate-900">
      <header className="bg-white border-b border-rose-100 px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-8 w-auto" />
            <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold">
              Portal Karyawan Saya (ESS)
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {divLink && (
              divLink.href.startsWith("/") ? (
                <Link href={divLink.href} className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold">
                  {divLink.label}
                </Link>
              ) : (
                <a href={divLink.href} className="px-3.5 py-2 rounded-xl bg-slate-900 text-white font-bold">
                  {divLink.label}
                </a>
              )
            )}
            <button onClick={() => { clearAuth(); router.push("/login"); }} className="px-3 py-2 rounded-xl border border-slate-200 font-semibold cursor-pointer">
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {msg && <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800">{msg}</div>}

        {/* Employee Identity Banner */}
        <div className="rounded-3xl bg-gradient-to-r from-[#88131D] to-[#E11D2E] text-white p-7 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="font-mono-num text-xs text-rose-200 font-bold">
              {data?.profile?.employee_code || user?.code} · {data?.profile?.department_code} · PTKP {data?.profile?.ptkp_status}
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-extrabold mt-1">
              {data?.profile?.full_name || user?.name}
            </h1>
            <p className="text-xs text-rose-100 mt-1">
              Role: <strong>{data?.profile?.role || user?.role}</strong> · Shift: {data?.profile?.shift_name} · Wilayah: {data?.profile?.city_code}
            </p>
          </div>
          <div className="bg-white/15 rounded-2xl px-5 py-3 text-center">
            <div className="text-[11px] text-rose-100">Skor KPI Saat Ini</div>
            <div className="font-mono-num text-2xl font-extrabold">{data?.profile?.kpi_score ?? "-"}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* GPS Check-In & Recent Attendance */}
          <div className="bg-white rounded-3xl border border-rose-100 p-6 space-y-4">
            <h2 className="font-display text-base font-extrabold">Absensi Harian (GPS)</h2>
            <div className="flex gap-2">
              <input value={gps} onChange={(e) => setGps(e.target.value)} className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num" />
              <button onClick={handleCheckIn} className="px-4 py-2 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold cursor-pointer shrink-0">
                Check-In Sekarang
              </button>
            </div>
            <div className="space-y-2 pt-2">
              <div className="text-xs font-bold text-slate-500">Riwayat Absensi Terakhir</div>
              {(data?.attendances || []).length === 0 ? (
                <div className="text-xs text-slate-400">Belum ada catatan absensi.</div>
              ) : (
                data.attendances.map((a: any, i: number) => (
                  <div key={i} className="p-2.5 rounded-xl bg-rose-50/40 text-xs flex justify-between">
                    <span className="font-mono-num font-bold">{a.date} · {a.check_in} WIB</span>
                    <span className="text-slate-600">{a.gps}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Private Personal Payslip */}
          <div className="bg-white rounded-3xl border border-rose-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-base font-extrabold">Slip Gaji Pribadi (Rahasia)</h2>
              <span className="font-mono-num text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold">
                Periode 2026-11
              </span>
            </div>
            {data?.slips?.[0] && (
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100"><span>Gaji Pokok</span><span className="font-mono-num font-semibold">{formatIDR(data.slips[0].base_salary)}</span></div>
                <div className="flex justify-between py-1 border-b border-slate-100"><span>Tunjangan Jabatan</span><span className="font-mono-num font-semibold">{formatIDR(data.slips[0].allowance)}</span></div>
                <div className="flex justify-between py-1 border-b border-slate-100"><span>Transport &amp; Makan</span><span className="font-mono-num font-semibold">{formatIDR(data.slips[0].transport_meal)}</span></div>
                <div className="flex justify-between py-1 border-b border-slate-100"><span>Lembur &amp; Insentif</span><span className="font-mono-num font-semibold">{formatIDR(data.slips[0].overtime_pay + data.slips[0].incentive_amount)}</span></div>
                <div className="flex justify-between py-1 border-b border-slate-100 text-red-600"><span>Potongan BPJS &amp; PPh 21</span><span className="font-mono-num font-semibold">-{formatIDR(data.slips[0].bpjs_employee + data.slips[0].pph21_amount)}</span></div>
                <div className="flex justify-between pt-2 text-sm font-extrabold text-emerald-700"><span>Take-Home Pay (Bersih)</span><span className="font-mono-num">{formatIDR(data.slips[0].net_salary)}</span></div>
              </div>
            )}
          </div>
        </div>

        {/* Leave Request Form */}
        <div className="bg-white rounded-3xl border border-rose-100 p-6">
          <h2 className="font-display text-base font-extrabold mb-3">Ajukan Cuti / Izin</h2>
          <form onSubmit={handleLeave} className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            <select value={leaveForm.leave_type} onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-xs">
              <option value="ANNUAL">Cuti Tahunan</option>
              <option value="SICK">Izin Sakit</option>
            </select>
            <input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num" />
            <input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num" />
            <input required value={leaveForm.reason} onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })} placeholder="Alasan cuti..." className="rounded-xl border border-slate-300 px-3 py-2 text-xs" />
            <button type="submit" className="rounded-xl bg-slate-900 hover:bg-[#E11D2E] text-white text-xs font-bold py-2 cursor-pointer">
              Kirim Pengajuan
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

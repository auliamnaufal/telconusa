"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { HR_ADMIN_ROLES, HRM_API, saveAuth } from "@/lib/auth";

const DEMO_USERS = [
  { label: "Nadia (Manajer HR)", email: "hr.manager@telconusa.id" },
  { label: "Rina (Teknisi)", email: "rina@telconusa.id" },
  { label: "Budi (Marketing)", email: "budi@telconusa.id" },
  { label: "Mirza (Finance)", email: "finance.manager@telconusa.id" },
  { label: "Raka (SCM)", email: "scm.manager@telconusa.id" },
];

export default function HRMLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("hr.manager@telconusa.id");
  const [password, setPassword] = useState("telconusa123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${HRM_API}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Email atau password karyawan salah");
      saveAuth(data.access_token, data.user);
      if (HR_ADMIN_ROLES.includes(data.user.role)) {
        router.push("/hr");
      } else {
        router.push("/karyawan");
      }
    } catch (err: any) {
      setError(err.message || "Gagal login ke HRM API");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-rose-50/40">
      {/* Left Warm Brand Panel */}
      <div className="lg:col-span-5 bg-gradient-to-br from-[#88131D] via-[#BE123C] to-[#E11D2E] text-white p-10 flex flex-col justify-between">
        <div>
          <img src="/brand/logos/telconusa-orbit-mono-white.svg" alt="TelcoNusa" className="h-10 w-auto mb-10" />
          <span className="px-3 py-1 rounded-full bg-white/15 text-[11px] font-bold uppercase tracking-wider">
            TelcoNusa People &amp; HRIS Platform
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-extrabold mt-4 leading-tight">
            Satu Akun Karyawan untuk Semua Layanan.
          </h1>
          <p className="text-rose-100 text-sm mt-4 leading-relaxed">
            HRM adalah sumber kebenaran identitas karyawan TelcoNusa. Login di sini untuk mengakses
            <strong> Portal Karyawan (Absensi GPS, Cuti, Slip Gaji Pribadi)</strong> atau{" "}
            <strong>Workspace Internal HR</strong> bagi tim HR &amp; Payroll.
          </p>
        </div>
        <div className="text-xs text-rose-200 pt-8 border-t border-white/15">
          © 2026 Divisi HRM · PT TelkoNusa Digital
        </div>
      </div>

      {/* Right Login Card */}
      <div className="lg:col-span-7 flex items-center justify-center p-6 sm:p-10">
        <div className="max-w-md w-full bg-white rounded-3xl border border-rose-100 p-8 shadow-xl shadow-rose-900/5">
          <h2 className="font-display text-2xl font-extrabold text-slate-900">Masuk HRIS &amp; Portal Karyawan</h2>
          <p className="text-xs text-slate-500 mt-1 mb-6">
            Gunakan akun karyawan tunggal Anda (password demo: <code className="font-mono-num font-bold">telconusa123</code>)
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Email Korporat</label>
              <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm" />
            </div>

            {error && <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">{error}</div>}

            <button disabled={loading} type="submit" className="w-full py-3 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer">
              {loading ? "Memverifikasi..." : "Masuk HRIS"}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              Tes Single-Account Login Berbagai Divisi:
            </div>
            <div className="flex flex-wrap gap-1.5">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.email}
                  type="button"
                  onClick={() => { setEmail(u.email); setPassword("telconusa123"); }}
                  className="px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-[#9F1239] text-[11px] font-semibold cursor-pointer"
                >
                  {u.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

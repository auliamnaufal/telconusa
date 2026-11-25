"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { FINANCE_ROLES, HRM_API, saveAuth } from "@/lib/auth";

export default function FinanceLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("finance.manager@telconusa.id");
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
      if (!res.ok) throw new Error(data.detail || "Email atau password salah");
      if (!FINANCE_ROLES.includes(data.user.role)) {
        throw new Error(`Akun Anda (${data.user.role}) tidak memiliki izin ke Finance Accounting Suite. Gunakan Portal Karyawan (:3002/karyawan) atau dashboard divisi Anda.`);
      }
      saveAuth(data.access_token, data.user);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Gagal login ke HRM Identity");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#090D16] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between mb-6">
          <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-8 w-auto" />
          <span className="px-2.5 py-1 rounded-md bg-rose-50 text-[#9F1239] font-mono-num text-[10px] font-extrabold">
            TREASURY &amp; GL
          </span>
        </div>

        <h1 className="font-display text-xl font-extrabold text-slate-900">
          Enterprise Finance &amp; Accounting Suite
        </h1>
        <p className="text-xs text-slate-500 mt-1 mb-6">
          Kelompok 3 · Login terpusat via HRM Identity untuk akses AR, AP, Buku Besar, &amp; Laporan Keuangan.
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

          <button disabled={loading} type="submit" className="w-full py-3 rounded-xl bg-[#0F172A] hover:bg-[#E11D2E] text-white font-display font-bold text-sm transition cursor-pointer">
            {loading ? "Memverifikasi..." : "Masuk Sistem Keuangan"}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100 flex flex-wrap gap-2 text-[11px]">
          <button type="button" onClick={() => { setEmail("finance.manager@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-rose-50 text-[#9F1239] font-bold cursor-pointer">
            Mirza (Manajer Keuangan)
          </button>
          <button type="button" onClick={() => { setEmail("direktur@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-semibold cursor-pointer">
            Hendra (Direktur Utama)
          </button>
        </div>
      </div>
    </div>
  );
}

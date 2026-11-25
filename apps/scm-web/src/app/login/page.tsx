"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { HRM_API, SCM_ROLES, saveAuth } from "@/lib/auth";

export default function SCMLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("scm.manager@telconusa.id");
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
      if (!SCM_ROLES.includes(data.user.role)) {
        throw new Error(`Role Anda (${data.user.role}) tidak memiliki akses ke SCM Control Tower. Gunakan Portal Karyawan (:3002/karyawan) atau dashboard divisi Anda.`);
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full rounded-3xl bg-slate-900 border border-slate-800 p-8 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-8 w-auto" />
          <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 font-mono-num text-[10px] font-bold text-rose-400">
            SCM CONTROL TOWER
          </span>
        </div>

        <h1 className="font-display text-xl font-extrabold text-white">Autentikasi Gudang &amp; Pengadaan</h1>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          Login menggunakan akun karyawan tunggal HRM (khusus tim SCM &amp; Direksi).
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1">Email Karyawan</label>
            <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1">Password</label>
            <input required type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl bg-slate-950 border border-slate-700 px-3.5 py-2.5 text-sm text-white" />
          </div>

          {error && <div className="rounded-xl bg-red-950/70 border border-red-700 text-red-200 text-xs p-3">{error}</div>}

          <button disabled={loading} type="submit" className="w-full py-3 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer">
            {loading ? "Memverifikasi..." : "Masuk Control Tower"}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800 flex flex-wrap gap-2 text-[11px]">
          <button type="button" onClick={() => { setEmail("scm.manager@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold cursor-pointer">
            Raka (Manajer SCM)
          </button>
          <button type="button" onClick={() => { setEmail("direktur@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold cursor-pointer">
            Hendra (Direktur)
          </button>
        </div>
      </div>
    </div>
  );
}

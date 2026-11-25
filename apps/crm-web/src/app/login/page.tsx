"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { CRM_STAFF_ROLES, HRM_API, saveAuth } from "@/lib/auth";

export default function CRMStaffLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("crm.manager@telconusa.id");
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
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Email atau password karyawan salah");

      const role = data.user.role;
      if (!CRM_STAFF_ROLES.includes(role)) {
        throw new Error(
          `Akun Anda (${role}) bukan tim CRM/Teknisi. Gunakan portal divisi Anda atau Portal Karyawan Terpusat (:3002/login).`
        );
      }

      saveAuth(data.access_token, data.user);
      if (role === "TECHNICIAN") {
        router.push("/teknisi");
      } else {
        router.push("/manager");
      }
    } catch (err: any) {
      setError(err.message || "Gagal login.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-5">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl">
        <div className="flex justify-center mb-4">
          <Link href="/login">
            <img src="/brand/logos/telconusa-orbit-stacked-light.svg" alt="TelcoNusa" className="h-24 w-auto" />
          </Link>
        </div>

        <div className="flex justify-center mb-3">
          <span className="px-3 py-1 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold uppercase tracking-wider">
            CRM Internal Portal · :3001
          </span>
        </div>

        <h1 className="font-display text-xl font-extrabold text-center text-slate-900">
          Login Portal Internal CRM &amp; Teknisi
        </h1>
        <p className="text-xs text-center text-slate-500 mt-1 mb-6">
          Gunakan 1 Akun Karyawan Terpusat (HRM SSO) untuk Manajer CRM, CS, Marketing, Sales, Direktur &amp; Teknisi Lapangan.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Karyawan (@telconusa.id)</label>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <input
              required
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
            />
          </div>

          {error && <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">{error}</div>}

          <button
            disabled={loading}
            type="submit"
            className="w-full py-3 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer disabled:opacity-50"
          >
            {loading ? "Memverifikasi HRM SSO..." : "Masuk ke CRM Internal"}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Akun Demo Internal CRM (Pass: telconusa123):
          </div>
          <div className="flex flex-wrap gap-1.5">
            <button type="button" onClick={() => { setEmail("crm.manager@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 text-[11px] font-semibold cursor-pointer">
              Dewi (Manajer CRM)
            </button>
            <button type="button" onClick={() => { setEmail("rina@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 text-[11px] font-semibold cursor-pointer">
              Rina (Teknisi)
            </button>
            <button type="button" onClick={() => { setEmail("budi@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 text-[11px] font-semibold cursor-pointer">
              Budi (Marketing)
            </button>
            <button type="button" onClick={() => { setEmail("direktur@telconusa.id"); setPassword("telconusa123"); }} className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 text-[11px] font-semibold cursor-pointer">
              Direktur
            </button>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <a href="http://localhost:3002/login" className="hover:text-[#E11D2E] font-semibold">
              Portal Karyawan (HRM ESS) →
            </a>
            <a href="http://localhost:3000" className="hover:text-[#E11D2E]">
              Website Pelanggan (:3000)
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

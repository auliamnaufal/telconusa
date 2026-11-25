"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CRM_API, getSafeNextPath, saveCustomerAuth } from "@/lib/auth";

function CustomerLoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const nextRaw = params.get("next");
  const nextPath = getSafeNextPath(nextRaw, "/portal");

  const [email, setEmail] = useState("andi@gmail.com");
  const [password, setPassword] = useState("telconusa123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${CRM_API}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Email atau password salah.");
      saveCustomerAuth(data.access_token, data.user);
      router.push(nextPath);
    } catch (err: any) {
      setError(err.message || "Gagal masuk ke akun pelanggan.");
    } finally {
      setLoading(false);
    }
  }

  const registerHref = nextRaw ? `/register?next=${encodeURIComponent(nextRaw)}` : "/register";

  return (
    <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-5">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl">
        <div className="flex justify-center mb-5">
          <Link href="/">
            <img src="/brand/logos/telconusa-orbit-stacked-light.svg" alt="TelcoNusa" className="h-24 w-auto" />
          </Link>
        </div>

        <h1 className="font-display text-xl font-extrabold text-center text-slate-900">
          Masuk ke Akun TelcoNusa
        </h1>
        <p className="text-xs text-center text-slate-500 mt-1 mb-6">
          Masuk ke akun pelanggan MyTelcoNusa untuk memesan layanan, melacak pemasangan, dan mengelola tagihan.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Pelanggan</label>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nama@email.com"
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
            {loading ? "Memverifikasi..." : "Masuk Sekarang"}
          </button>
        </form>

        <div className="mt-5 text-center text-xs text-slate-600">
          Belum punya akun?{" "}
          <Link href={registerHref} className="font-bold text-[#E11D2E] hover:underline">
            Daftar Pelanggan Baru →
          </Link>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Akun Uji Pelanggan:
            </div>
            <button
              type="button"
              onClick={() => {
                setEmail("andi@gmail.com");
                setPassword("telconusa123");
              }}
              className="mt-1 px-2.5 py-1 rounded-lg bg-rose-50 text-[#BE123C] text-[11px] font-bold cursor-pointer"
            >
              Pak Andi (CUS-000456)
            </button>
          </div>
          <Link href="/" className="text-xs font-semibold text-slate-500 hover:text-[#E11D2E]">
            ← Beranda
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function CustomerLoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#070B14]" />}>
      <CustomerLoginForm />
    </Suspense>
  );
}

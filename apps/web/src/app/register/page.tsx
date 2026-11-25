"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CRM_API, getSafeNextPath, saveCustomerAuth } from "@/lib/auth";

function CustomerRegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const nextRaw = params.get("next");
  const nextPath = getSafeNextPath(nextRaw, "/portal");

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    whatsapp_number: "628",
    nik_or_npwp: "",
    password: "",
    confirm_password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      setError("Konfirmasi password tidak cocok.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${CRM_API}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: form.full_name,
          email: form.email,
          whatsapp_number: form.whatsapp_number,
          nik_or_npwp: form.nik_or_npwp.trim() || null,
          password: form.password,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Pendaftaran gagal.");
      saveCustomerAuth(data.access_token, data.user);
      router.push(nextPath);
    } catch (err: any) {
      setError(err.message || "Gagal mendaftarkan akun.");
    } finally {
      setLoading(false);
    }
  }

  const loginHref = nextRaw ? `/login?next=${encodeURIComponent(nextRaw)}` : "/login";

  return (
    <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-5">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl">
        <div className="flex justify-center mb-4">
          <Link href="/">
            <img src="/brand/logos/telconusa-orbit-stacked-light.svg" alt="TelcoNusa" className="h-20 w-auto" />
          </Link>
        </div>

        <h1 className="font-display text-xl font-extrabold text-center text-slate-900">
          Daftar Akun Pelanggan TelcoNusa
        </h1>
        <p className="text-xs text-center text-slate-500 mt-1 mb-5">
          Buat akun MyTelcoNusa untuk memesan paket Fiber/5G+ dan memantau jadwal pemasangan teknisi.
        </p>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Nama Lengkap</label>
            <input
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Contoh: Raka Mahendra"
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Email Aktif</label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="raka@email.com"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Nomor WhatsApp</label>
              <input
                required
                value={form.whatsapp_number}
                onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                placeholder="62812..."
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-mono-num"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">NIK / NPWP (Opsional)</label>
            <input
              value={form.nik_or_npwp}
              onChange={(e) => setForm({ ...form, nik_or_npwp: e.target.value })}
              placeholder="16 digit NIK untuk administrasi instalasi"
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-mono-num"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <input
                required
                minLength={6}
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Min. 6 karakter"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Ulangi Password</label>
              <input
                required
                minLength={6}
                type="password"
                value={form.confirm_password}
                onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                placeholder="Ketik ulang"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm"
              />
            </div>
          </div>

          {error && <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">{error}</div>}

          <button
            disabled={loading}
            type="submit"
            className="w-full py-3 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer disabled:opacity-50"
          >
            {loading ? "Mendaftarkan Akun..." : "Daftar & Lanjutkan"}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
          <span>
            Sudah punya akun?{" "}
            <Link href={loginHref} className="font-bold text-[#E11D2E] hover:underline">
              Masuk di sini
            </Link>
          </span>
          <Link href="/" className="font-semibold text-slate-500 hover:text-[#E11D2E]">
            ← Beranda
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function CustomerRegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#070B14]" />}>
      <CustomerRegisterForm />
    </Suspense>
  );
}

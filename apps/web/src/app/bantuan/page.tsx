"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CSWidget from "@/components/CSWidget";
import { CRM_API, CustomerUser, getCustomerAuth } from "@/lib/auth";

const QUICK_TOPICS = [
  { priority: "P1", subject: "Modem ONT Berkedip Merah (LOS)", label: "Internet Mati / LOS (P1)" },
  { priority: "P3", subject: "Koneksi Wi-Fi Terasa Lambat", label: "Koneksi Lambat (P3)" },
  { priority: "P3", subject: "Tanya Ketersediaan & Jadwal Pasang Baru", label: "Info Pemasangan (P3)" },
  { priority: "P4", subject: "Konfirmasi Tagihan & Nomor Virtual Account", label: "Tagihan & VA (P4)" },
];

export default function BantuanPage() {
  const [user, setUser] = useState<CustomerUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    whatsapp_number: "628",
    priority: "P3",
    subject: "",
    description: "",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const auth = getCustomerAuth();
    if (auth.token && auth.user && auth.user.role === "CUSTOMER") {
      setToken(auth.token);
      setUser(auth.user);
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const isLogged = Boolean(token && user);
      const url = isLogged ? `${CRM_API}/api/v1/tickets` : `${CRM_API}/api/v1/public/support`;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (isLogged && token) headers.Authorization = `Bearer ${token}`;

      const payload = isLogged
        ? { priority: form.priority, subject: form.subject, description: form.description }
        : form;

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Gagal mengirim tiket bantuan.");
      setResult(json);
      setForm({ full_name: "", email: "", whatsapp_number: "628", priority: "P3", subject: "", description: "" });
    } catch (err: any) {
      setError(err.message || "Gagal terhubung ke layanan CS TelcoNusa.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3">
            <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-8 w-auto" />
            <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold">
              Pusat Bantuan &amp; Layanan CS 24/7
            </span>
          </Link>
          <div className="flex items-center gap-3 text-xs font-bold">
            <Link href="/" className="text-slate-600 hover:text-[#E11D2E]">← Beranda</Link>
            <Link href="/portal" className="px-3.5 py-2 rounded-xl bg-slate-900 text-white">MyTelcoNusa</Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 py-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-5 space-y-5">
          <div className="rounded-3xl bg-[#070B14] text-white p-7 space-y-4">
            <span className="px-3 py-1 rounded-full bg-white/10 text-[#FF8A95] text-[11px] font-bold uppercase tracking-wider">
              Standar Layanan Pelanggan
            </span>
            <h1 className="font-display text-2xl font-extrabold">
              Layanan Customer Care TelcoNusa 24/7
            </h1>
            <p className="text-xs text-slate-300 leading-relaxed">
              Setiap keluhan atau pertanyaan dari halaman ini masuk langsung ke antrean agen Customer Service kami dan mendapatkan nomor tiket pelacakan resmi.
            </p>
            <div className="space-y-2.5 pt-2 text-xs">
              <div className="rounded-2xl bg-white/5 border border-white/10 p-3.5">
                <div className="font-bold text-white">Prioritas P1 / P2 — Gangguan Berat</div>
                <div className="text-slate-300 mt-0.5">Penanganan darurat &lt; 15 menit &amp; eskalasi teknisi lapangan.</div>
              </div>
              <div className="rounded-2xl bg-white/5 border border-white/10 p-3.5">
                <div className="font-bold text-white">Prioritas P3 / P4 — Konsultasi &amp; Tagihan</div>
                <div className="text-slate-300 mt-0.5">Info cakupan wilayah, upgrade paket, dan verifikasi VA Finance.</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-slate-200 p-6">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Topik Cepat</div>
            <div className="flex flex-wrap gap-2">
              {QUICK_TOPICS.map((t) => (
                <button
                  key={t.label}
                  type="button"
                  onClick={() => setForm({ ...form, priority: t.priority, subject: t.subject })}
                  className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-[#BE123C] text-xs font-semibold cursor-pointer transition"
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200 p-7 shadow-sm">
          <h2 className="font-display text-xl font-extrabold text-slate-900">
            Ajukan Tiket Bantuan Pelanggan
          </h2>
          <p className="text-xs text-slate-500 mt-1 mb-5">
            Isi formulir di bawah ini. Jika Anda sudah masuk ke MyTelcoNusa, data akun Anda otomatis terhubung.
          </p>

          {result ? (
            <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-6 space-y-3">
              <div className="font-display text-lg font-extrabold text-emerald-900">
                ✓ Tiket Bantuan Berhasil Terdaftar!
              </div>
              <div className="text-sm text-emerald-800 space-y-1 font-mono-num">
                <div>Kode Tiket: <strong>{result.ticket_code}</strong></div>
                <div>Prioritas: <strong>{result.priority}</strong></div>
                <div>Status: <strong>{result.status}</strong></div>
              </div>
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setResult(null)}
                  className="px-4 py-2 rounded-xl bg-emerald-700 text-white text-xs font-bold cursor-pointer"
                >
                  Buat Tiket Lain
                </button>
                <Link href="/portal" className="px-4 py-2 rounded-xl border border-emerald-300 bg-white text-emerald-900 text-xs font-bold">
                  Cek Status di MyTelcoNusa →
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {user ? (
                <div className="rounded-2xl bg-rose-50 border border-rose-200 p-4 text-xs text-[#9F1239]">
                  Akun Terhubung: <strong>{user.name}</strong> ({user.code} · {user.email})
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Nama Lengkap</label>
                    <input
                      required
                      value={form.full_name}
                      onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Email Aktif</label>
                    <input
                      required
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">No. WhatsApp</label>
                    <input
                      value={form.whatsapp_number}
                      onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm font-mono-num"
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Prioritas</label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                  >
                    <option value="P1">P1 — Darurat / LOS Merah</option>
                    <option value="P2">P2 — Internet Mati</option>
                    <option value="P3">P3 — Lambat / Tanya Layanan</option>
                    <option value="P4">P4 — Tagihan &amp; VA</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 mb-1">Subjek</label>
                  <input
                    required
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    placeholder="Ringkas permasalahan Anda"
                    className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Deskripsi Lengkap</label>
                <textarea
                  required
                  rows={4}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Jelaskan detail gangguan, alamat, atau nomor order Anda..."
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                />
              </div>

              {error && <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">{error}</div>}

              <button
                disabled={loading}
                type="submit"
                className="w-full py-3.5 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer disabled:opacity-50"
              >
                {loading ? "Mengirim Tiket..." : "Kirim Tiket ke Layanan CS"}
              </button>
            </form>
          )}
        </div>
      </main>

      <CSWidget />
    </div>
  );
}

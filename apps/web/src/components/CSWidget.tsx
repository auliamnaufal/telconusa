"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CRM_API, CustomerUser, getCustomerAuth } from "@/lib/auth";

export default function CSWidget() {
  const [open, setOpen] = useState(false);
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
  const [ticketResult, setTicketResult] = useState<{ ticket_code: string; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const auth = getCustomerAuth();
    if (auth.token && auth.user && auth.user.role === "CUSTOMER") {
      setToken(auth.token);
      setUser(auth.user);
    }
  }, [open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const isLoggedIn = Boolean(token && user && user.role === "CUSTOMER");
      const url = isLoggedIn ? `${CRM_API}/api/v1/tickets` : `${CRM_API}/api/v1/public/support`;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (isLoggedIn && token) headers.Authorization = `Bearer ${token}`;

      const payload = isLoggedIn
        ? {
            priority: form.priority,
            subject: form.subject,
            description: form.description,
          }
        : form;

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal mengirim tiket CS.");
      setTicketResult({ ticket_code: data.ticket_code, status: data.status });
      setForm({
        full_name: "",
        email: "",
        whatsapp_number: "628",
        priority: "P3",
        subject: "",
        description: "",
      });
    } catch (err: any) {
      setError(err.message || "Gagal terhubung ke layanan CS TelcoNusa.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end">
      {open && (
        <div className="mb-3 w-[340px] sm:w-[380px] rounded-3xl bg-white border border-slate-200 shadow-2xl overflow-hidden">
          <div className="bg-gradient-to-r from-[#0F172A] via-[#88131D] to-[#E11D2E] text-white px-5 py-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-rose-200">
                Customer Care 24/7
              </div>
              <div className="font-display font-extrabold text-sm">Layanan CS TelcoNusa</div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Tutup widget CS"
              className="w-7 h-7 rounded-full bg-white/15 hover:bg-white/25 text-xs font-bold flex items-center justify-center cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="p-4 max-h-[70vh] overflow-y-auto">
            {ticketResult ? (
              <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-4 space-y-2.5 text-xs">
                <div className="font-display font-extrabold text-emerald-900 text-sm">
                  ✓ Tiket Bantuan Diterima!
                </div>
                <p className="text-emerald-800">
                  Kode Tiket Anda: <strong className="font-mono-num">{ticketResult.ticket_code}</strong> ({ticketResult.status}). Tim CS CRM kami segera menindaklanjuti laporan Anda.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setTicketResult(null)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-700 text-white font-bold cursor-pointer"
                  >
                    Kirim Tiket Lain
                  </button>
                  <Link
                    href="/bantuan"
                    className="px-3 py-1.5 rounded-lg bg-white border border-emerald-300 text-emerald-900 font-bold"
                  >
                    Pusat Bantuan →
                  </Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3 text-xs">
                {user ? (
                  <div className="rounded-xl bg-rose-50 border border-rose-200 px-3 py-2 text-[#9F1239] font-semibold">
                    Masuk sebagai: <strong>{user.name}</strong> ({user.code})
                  </div>
                ) : (
                  <>
                    <div>
                      <label className="block font-bold text-slate-700 mb-1">Nama Lengkap</label>
                      <input
                        required
                        value={form.full_name}
                        onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                        placeholder="Contoh: Nadia Putri"
                        className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Email</label>
                        <input
                          required
                          type="email"
                          value={form.email}
                          onChange={(e) => setForm({ ...form, email: e.target.value })}
                          placeholder="email@anda.com"
                          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">No. WhatsApp</label>
                        <input
                          value={form.whatsapp_number}
                          onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value })}
                          placeholder="62812..."
                          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs font-mono-num"
                        />
                      </div>
                    </div>
                  </>
                )}

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Kategori / Prioritas</label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: e.target.value })}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
                  >
                    <option value="P1">P1 — Gangguan Mendesak / LOS Merah</option>
                    <option value="P2">P2 — Internet Putus Total</option>
                    <option value="P3">P3 — Pertanyaan Paket / Koneksi Lambat</option>
                    <option value="P4">P4 — Tagihan &amp; Administrasi Akun</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Subjek Bantuan</label>
                  <input
                    required
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    placeholder="Contoh: Tanya jadwal pemasangan area Bandung"
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Pesan / Detail Kendala</label>
                  <textarea
                    required
                    rows={3}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="Ceritakan kebutuhan atau kendala Anda..."
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs"
                  />
                </div>

                {error && (
                  <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 p-2.5 text-[11px]">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-xs cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Mengirim ke CS CRM..." : "Kirim ke Layanan CS 24/7"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2.5 px-5 py-3.5 rounded-full bg-[#0F172A] hover:bg-[#E11D2E] text-white shadow-2xl border border-white/15 font-display font-bold text-xs transition cursor-pointer"
      >
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
        <span>Layanan CS 24/7</span>
      </button>
    </div>
  );
}

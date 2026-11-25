"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import CSWidget from "@/components/CSWidget";
import { CRM_API, CustomerUser, clearCustomerAuth, formatIDR, getCustomerAuth } from "@/lib/auth";

const STEPS = [
  { key: "SUBMITTED", label: "Order Diterima" },
  { key: "PAID", label: "Pembayaran Lunas" },
  { key: "IN_PROGRESS", label: "Teknisi Bertugas" },
  { key: "COMPLETED", label: "Layanan Aktif" },
];

function getStepIndex(orderStatus: string, installStatus: string): number {
  if (installStatus === "COMPLETED" || orderStatus === "COMPLETED") return 3;
  if (installStatus === "IN_PROGRESS") return 2;
  if (orderStatus === "PAID") return 1;
  return 0;
}

export default function CustomerPortalPage() {
  const router = useRouter();
  const [user, setUser] = useState<CustomerUser | null>(null);
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [ticketForm, setTicketForm] = useState({ priority: "P2", subject: "", description: "" });
  const [ratingChoice, setRatingChoice] = useState<Record<string, { score: number; comment: string }>>({});

  async function loadPortal(token: string) {
    const res = await fetch(`${CRM_API}/api/v1/portal/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (res.status === 401 || res.status === 403) {
      clearCustomerAuth();
      router.replace("/login?next=/portal");
      return;
    }
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    const { token, user: u } = getCustomerAuth();
    if (!token || !u || u.role !== "CUSTOMER") {
      router.replace("/login?next=/portal");
      return;
    }
    setUser(u);
    loadPortal(token);
  }, []);

  async function handleTicket(e: React.FormEvent) {
    e.preventDefault();
    const { token } = getCustomerAuth();
    if (!token) return;
    const res = await fetch(`${CRM_API}/api/v1/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(ticketForm),
    });
    if (res.ok) {
      const json = await res.json();
      setMsg(`Tiket keluhan ${json.ticket_code} berhasil dibuat & masuk antrean Layanan CS!`);
      setTicketForm({ priority: "P2", subject: "", description: "" });
      loadPortal(token);
    }
  }

  async function submitRating(woId: string) {
    const { token } = getCustomerAuth();
    if (!token) return;
    const choice = ratingChoice[woId] || { score: 5, comment: "Pelayanan sangat rapi dan cepat!" };
    const res = await fetch(`${CRM_API}/api/v1/ratings`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ work_order_id: woId, rating_score: choice.score, rating_comment: choice.comment }),
    });
    if (res.ok) {
      setMsg("Terima kasih! Penilaian teknisi berhasil dikirim.");
      loadPortal(token);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/">
              <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-8 w-auto" />
            </Link>
            <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold">
              MyTelcoNusa · Portal Pelanggan
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="font-semibold text-slate-600 hidden sm:inline">Halo, {user?.name}</span>
            <Link href="/bantuan" className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-slate-700">
              Pusat Bantuan
            </Link>
            <Link href="/order" className="px-3.5 py-2 rounded-xl bg-[#E11D2E] text-white font-bold">
              + Tambah Paket
            </Link>
            <button
              onClick={() => {
                clearCustomerAuth();
                router.push("/login");
              }}
              className="px-3 py-2 rounded-xl border border-slate-200 font-semibold cursor-pointer"
            >
              Keluar
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        {msg && <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800">{msg}</div>}

        <div className="rounded-3xl bg-gradient-to-r from-[#0F172A] via-[#88131D] to-[#E11D2E] text-white p-7 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="text-[11px] uppercase tracking-widest text-rose-200 font-bold">
              Pelanggan {data?.customer?.customer_code || user?.code} · {data?.customer?.segment || "INDIVIDUAL"}
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-extrabold mt-1">
              {data?.subscriptions?.[0] ? `${data.subscriptions[0].sku} — Aktif` : "Selamat Datang di MyTelcoNusa"}
            </h1>
            <p className="text-xs text-rose-100 mt-1">
              Alamat Utama: {data?.addresses?.[0]?.install_address || "Belum ada alamat pemasangan terdaftar"}
            </p>
          </div>
          <div className="bg-white/10 border border-white/15 rounded-2xl px-5 py-4 backdrop-blur-sm">
            <div className="text-[11px] text-rose-200">Tagihan Terakhir</div>
            <div className="font-mono-num text-xl font-extrabold mt-0.5">
              {data?.invoices?.[0] ? formatIDR(data.invoices[0].total) : "Rp0"}
            </div>
            <div className="text-[11px] font-mono-num mt-1">
              VA: {data?.invoices?.[0]?.virtual_account || "-"} · {data?.invoices?.[0]?.status || "SIAP"}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200 p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-extrabold">Status Pemasangan &amp; Penilaian Teknisi</h2>
            <Link href="/order?sku=HOME-50" className="text-xs font-bold text-[#E11D2E] hover:underline">
              + Pesan Paket Baru
            </Link>
          </div>

          {(data?.work_orders || []).length === 0 ? (
            <div className="rounded-2xl bg-slate-50 border border-slate-200 p-6 text-center space-y-3">
              <div className="font-display font-bold text-slate-800">Belum ada pesanan pemasangan</div>
              <p className="text-xs text-slate-500">Mulai berlangganan TelcoHome Fiber atau paket 5G+ pertama Anda.</p>
              <Link href="/order?sku=HOME-50" className="inline-block px-5 py-2.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold">
                Pesan TelcoHome Fiber →
              </Link>
            </div>
          ) : (
            (data?.work_orders || []).map((w: any) => {
              const activeStep = getStepIndex(w.order_status, w.installation_status);
              const curr = ratingChoice[w.id] || { score: w.rating_score || 5, comment: w.rating_comment || "" };
              return (
                <div key={w.id} className="rounded-2xl border border-slate-200 p-5 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="font-mono-num text-sm font-bold">{w.work_order_code} · Paket {w.sku}</div>
                      <div className="text-xs text-slate-500">{w.install_address} · Teknisi: {w.technician_employee_id || "Menunggu Penugasan"}</div>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-rose-50 text-[#BE123C] text-xs font-bold">
                      {w.order_status === "ON_HOLD" ? "Pending — Menunggu Stok" : w.installation_status}
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 pt-2">
                    {STEPS.map((st, idx) => (
                      <div key={st.key} className="text-center">
                        <div className={`h-2 rounded-full mb-1.5 ${idx <= activeStep ? "bg-[#E11D2E]" : "bg-slate-200"}`} />
                        <span className={`text-[11px] font-semibold ${idx <= activeStep ? "text-slate-900" : "text-slate-400"}`}>
                          {st.label}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-700 mr-2">Beri Rating Teknisi:</span>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRatingChoice({ ...ratingChoice, [w.id]: { ...curr, score: star } })}
                          className={`text-xl cursor-pointer ${star <= curr.score ? "text-amber-500" : "text-slate-300"}`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                    <div className="flex gap-2 flex-1 max-w-md">
                      <input
                        value={curr.comment}
                        onChange={(e) => setRatingChoice({ ...ratingChoice, [w.id]: { ...curr, comment: e.target.value } })}
                        placeholder="Tulis ulasan layanan teknisi..."
                        className="flex-1 rounded-xl border border-slate-300 px-3 py-1.5 text-xs"
                      />
                      <button
                        onClick={() => submitRating(w.id)}
                        className="px-4 py-1.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold cursor-pointer"
                      >
                        Kirim Rating
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-3xl border border-slate-200 p-6">
            <h2 className="font-display text-base font-extrabold mb-4">Alamat Pemasangan &amp; Tiket Saya</h2>
            <div className="space-y-3 mb-4">
              {(data?.addresses || []).length === 0 ? (
                <div className="text-xs text-slate-500">Belum ada alamat terdaftar.</div>
              ) : (
                (data?.addresses || []).map((a: any) => (
                  <div key={a.address_code} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 text-xs">
                    <div className="font-bold text-slate-900">{a.label} ({a.city_code} · {a.postal_code})</div>
                    <div className="text-slate-600 mt-0.5">{a.install_address}</div>
                  </div>
                ))
              )}
            </div>
            {(data?.tickets || []).length > 0 && (
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <div className="text-xs font-bold text-slate-600">Riwayat Tiket Layanan CS:</div>
                {(data?.tickets || []).map((t: any) => (
                  <div key={t.ticket_code} className="p-2.5 rounded-xl bg-rose-50/50 border border-rose-100 text-xs flex justify-between">
                    <span className="font-semibold">{t.ticket_code} · {t.subject}</span>
                    <span className="font-mono-num font-bold text-[#BE123C]">{t.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white rounded-3xl border border-slate-200 p-6">
            <h2 className="font-display text-base font-extrabold mb-3">Ajukan Keluhan / Tiket Layanan CS</h2>
            <form onSubmit={handleTicket} className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <select value={ticketForm.priority} onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-xs">
                  <option value="P2">P2 — Internet Mati</option>
                  <option value="P3">P3 — Koneksi Lambat</option>
                  <option value="P4">P4 — Tagihan</option>
                </select>
                <input required value={ticketForm.subject} onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })} placeholder="Subjek keluhan..." className="col-span-2 rounded-xl border border-slate-300 px-3 py-2 text-xs" />
              </div>
              <textarea required rows={2} value={ticketForm.description} onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })} placeholder="Jelaskan kendala Anda..." className="w-full rounded-xl border border-slate-300 px-3 py-2 text-xs" />
              <button type="submit" className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-[#E11D2E] text-white text-xs font-bold cursor-pointer">
                Kirim Tiket ke CS
              </button>
            </form>
          </div>
        </div>
      </main>

      <CSWidget />
    </div>
  );
}

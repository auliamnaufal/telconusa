"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import CSWidget from "@/components/CSWidget";
import {
  CRM_API,
  CustomerUser,
  HRM_API,
  clearCustomerAuth,
  formatIDR,
  getCustomerAuth,
} from "@/lib/auth";

const PLANS = [
  { sku: "HOME-20", name: "TelcoHome Fiber 20 Mbps", price: 250000, line: "HOME" },
  { sku: "HOME-50", name: "TelcoHome Fiber 50 Mbps", price: 400000, line: "HOME" },
  { sku: "HOME-100", name: "TelcoHome Fiber 100 Mbps", price: 600000, line: "HOME" },
  { sku: "MOB-PRE-10", name: "Prabayar 5G 10 GB", price: 50000, line: "PREPAID" },
  { sku: "MOB-PRE-50", name: "Prabayar 5G 50 GB", price: 150000, line: "PREPAID" },
  { sku: "MOB-POST-50", name: "Pascabayar Priority 50 GB", price: 175000, line: "POSTPAID" },
];

function OrderFormContent() {
  const params = useSearchParams();
  const initialSku = params.get("sku") || "HOME-50";
  const initialRef = params.get("ref") || "";

  const [authReady, setAuthReady] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<CustomerUser | null>(null);

  const [form, setForm] = useState({
    install_address: "",
    city_code: "BDG",
    postal_code: "40132",
    sku: initialSku,
    referral_code: initialRef || "REF-EMP0017",
  });
  const [refInfo, setRefInfo] = useState<{ valid: boolean; name?: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const auth = getCustomerAuth();
    if (auth.token && auth.user && auth.user.role === "CUSTOMER") {
      setToken(auth.token);
      setUser(auth.user);
    }
    setAuthReady(true);
  }, []);

  const selectedPlan = PLANS.find((p) => p.sku === form.sku) || PLANS[1];
  const installFee = selectedPlan.line === "HOME" ? 150000 : 0;
  const subtotal = selectedPlan.price + installFee;
  const tax = Math.round(subtotal * 0.11);
  const grandTotal = subtotal + tax;

  const returnPath = `/order?sku=${encodeURIComponent(form.sku)}${initialRef ? `&ref=${encodeURIComponent(initialRef)}` : ""}`;
  const encodedNext = encodeURIComponent(returnPath);

  async function verifyReferral() {
    if (!form.referral_code.trim()) return;
    try {
      const r = await fetch(`${HRM_API}/api/v1/referrals/${encodeURIComponent(form.referral_code.trim())}`, {
        cache: "no-store",
      });
      if (r.ok) {
        const d = await r.json();
        setRefInfo({ valid: true, name: `${d.employee_name} (${d.employee_code})` });
      } else {
        setRefInfo({ valid: false });
      }
    } catch {
      setRefInfo({ valid: false });
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${CRM_API}/api/v1/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          install_address: form.install_address,
          city_code: form.city_code,
          postal_code: form.postal_code,
          sku: form.sku,
          referral_code: form.referral_code.trim() || null,
        }),
      });
      if (res.status === 401) {
        clearCustomerAuth();
        setToken(null);
        setUser(null);
        setError("Sesi login Anda berakhir. Silakan masuk atau daftar kembali.");
        return;
      }
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Gagal mengirim order.");
      setResult(json);
    } catch (err: any) {
      setError(err.message || "Gagal terhubung ke layanan pemesanan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/">
            <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-9 w-auto" />
          </Link>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <Link href="/bantuan" className="text-slate-600 hover:text-[#E11D2E]">
              Butuh Bantuan CS?
            </Link>
            <Link href="/" className="text-slate-600 hover:text-[#E11D2E]">
              ← Kembali ke Beranda
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200 p-7 shadow-sm">
            {!authReady ? (
              <div className="py-12 text-center text-sm text-slate-500">Memeriksa sesi akun Anda...</div>
            ) : !token || !user ? (
              <div className="space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold uppercase tracking-wider">
                  Pendaftaran Akun Diperlukan
                </div>
                <h1 className="font-display text-2xl font-extrabold text-slate-900">
                  Daftar atau Masuk Sebelum Memesan Layanan
                </h1>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Untuk keamanan transaksi dan kenyamanan pelacakan jadwal teknisi serta pembayaran Virtual Account, setiap pemesanan layanan TelcoNusa wajib terhubung ke akun pelanggan Anda.
                </p>

                <div className="rounded-2xl bg-slate-50 border border-slate-200 p-4 text-xs text-slate-700 space-y-1.5">
                  <div className="font-bold text-slate-900">Yang Anda dapatkan di akun MyTelcoNusa:</div>
                  <div>✓ Pantau jadwal kedatangan teknisi secara real-time</div>
                  <div>✓ Kelola beberapa alamat pemasangan dalam satu akun</div>
                  <div>✓ Akses invoice PPN 11%, nomor Virtual Account, &amp; riwayat tiket CS 24/7</div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 pt-2">
                  <Link
                    href={`/register?next=${encodedNext}`}
                    className="flex-1 text-center py-3.5 px-5 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm shadow-md shadow-red-600/20 transition"
                  >
                    Daftar Akun Baru →
                  </Link>
                  <Link
                    href={`/login?next=${encodedNext}`}
                    className="flex-1 text-center py-3.5 px-5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-display font-bold text-sm transition"
                  >
                    Masuk Akun Pelanggan
                  </Link>
                </div>
              </div>
            ) : result ? (
              <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-6 space-y-3">
                <div className="font-display text-lg font-extrabold text-emerald-800">
                  ✓ Pemesanan Berhasil Diterima!
                </div>
                <div className="text-sm text-emerald-950 space-y-1.5 font-mono-num">
                  <div>No. Order: <strong>{result.order_no}</strong></div>
                  <div>Kode Pelanggan: <strong>{result.customer_code}</strong></div>
                  <div>Work Order Teknisi: <strong>{result.work_order_code}</strong></div>
                  <div>Status Order: <strong>{result.status}</strong></div>
                  <div>Total Tagihan (+PPN 11%): <strong>{formatIDR(result.estimated_total_with_ppn)}</strong></div>
                </div>
                <div className="pt-3 flex flex-wrap gap-3">
                  <Link href="/portal" className="px-4 py-2.5 rounded-xl bg-[#E11D2E] text-white text-xs font-bold">
                    Pantau di MyTelcoNusa →
                  </Link>
                  <button
                    onClick={() => setResult(null)}
                    className="px-4 py-2.5 rounded-xl border border-slate-300 text-xs font-semibold cursor-pointer"
                  >
                    Buat Order Baru
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h1 className="font-display text-2xl font-extrabold text-slate-900">
                  Checkout Layanan Personal
                </h1>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Pesanan diterbitkan resmi atas akun pelanggan Anda dan langsung dijadwalkan untuk pemasangan.
                </p>

                <div className="rounded-2xl bg-rose-50 border border-rose-200 p-4 mb-5 flex items-center justify-between gap-3 text-xs">
                  <div>
                    <div className="font-bold text-[#9F1239]">
                      Pemesan: {user.name} ({user.code})
                    </div>
                    <div className="text-slate-600 mt-0.5">
                      {user.email} {user.whatsapp_number ? `· ${user.whatsapp_number}` : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      clearCustomerAuth();
                      setToken(null);
                      setUser(null);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-white border border-rose-200 text-[#BE123C] font-bold cursor-pointer shrink-0"
                  >
                    Ganti Akun
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Paket Layanan</label>
                    <select
                      value={form.sku}
                      onChange={(e) => setForm({ ...form, sku: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    >
                      {PLANS.map((p) => (
                        <option key={p.sku} value={p.sku}>
                          {p.sku} — {p.name} ({formatIDR(p.price)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Alamat Pemasangan (Wajib — tiap layanan dapat memiliki alamat berbeda)
                    </label>
                    <textarea
                      required
                      rows={2}
                      value={form.install_address}
                      onChange={(e) => setForm({ ...form, install_address: e.target.value })}
                      placeholder="Jl. Setiabudi No. 45, Bandung..."
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Kota Cakupan</label>
                      <select
                        value={form.city_code}
                        onChange={(e) => setForm({ ...form, city_code: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                      >
                        <option value="JKT">Jakarta (JKT)</option>
                        <option value="BDG">Bandung (BDG)</option>
                        <option value="SBY">Surabaya (SBY)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Kode Pos</label>
                      <input
                        required
                        value={form.postal_code}
                        onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
                        className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm font-mono-num"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Kode Referral Marketing (Opsional)</label>
                    <div className="flex gap-2">
                      <input
                        value={form.referral_code}
                        onChange={(e) => {
                          setForm({ ...form, referral_code: e.target.value });
                          setRefInfo(null);
                        }}
                        placeholder="Mis. REF-EMP0017"
                        className="flex-1 rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm font-mono-num"
                      />
                      <button
                        type="button"
                        onClick={verifyReferral}
                        className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold cursor-pointer"
                      >
                        Cek Kode
                      </button>
                    </div>
                    {refInfo && (
                      <div className={`text-xs mt-1.5 font-semibold ${refInfo.valid ? "text-emerald-700" : "text-red-600"}`}>
                        {refInfo.valid ? `✓ Terverifikasi milik ${refInfo.name}` : "✕ Kode referral tidak ditemukan di HRM"}
                      </div>
                    )}
                  </div>

                  {error && <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">{error}</div>}

                  <button
                    disabled={loading}
                    type="submit"
                    className="w-full py-3.5 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer disabled:opacity-50"
                  >
                    {loading ? "Memproses Pesanan..." : "Konfirmasi & Terbitkan Tagihan"}
                  </button>
                </form>
              </>
            )}
          </div>

          <aside className="lg:col-span-5 bg-white rounded-3xl border border-slate-200 p-7 shadow-sm sticky top-8">
            <div className="text-xs font-bold uppercase tracking-wider text-[#E11D2E]">Ringkasan Transparan</div>
            <h2 className="font-display text-lg font-extrabold mt-1 mb-5">{selectedPlan.name}</h2>
            <div className="space-y-3 text-sm border-b border-slate-100 pb-4">
              <div className="flex justify-between">
                <span className="text-slate-500">Harga Paket ({selectedPlan.sku})</span>
                <span className="font-mono-num font-bold">{formatIDR(selectedPlan.price)}</span>
              </div>
              {installFee > 0 && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Biaya Instalasi &amp; Aktivasi</span>
                  <span className="font-mono-num font-bold">{formatIDR(installFee)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-500">Subtotal (DPP)</span>
                <span className="font-mono-num font-semibold">{formatIDR(subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">PPN 11%</span>
                <span className="font-mono-num font-semibold">{formatIDR(tax)}</span>
              </div>
            </div>
            <div className="flex justify-between items-center pt-4">
              <span className="font-display font-bold">Total Pembayaran</span>
              <span className="font-mono-num text-2xl font-extrabold text-[#E11D2E]">{formatIDR(grandTotal)}</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-4">
              *Nomor Virtual Account diterbitkan otomatis setelah pemesanan dikonfirmasi.
            </p>
          </aside>
        </div>
      </div>

      <CSWidget />
    </div>
  );
}

export default function OrderPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center text-sm">Memuat checkout...</div>}>
      <OrderFormContent />
    </Suspense>
  );
}

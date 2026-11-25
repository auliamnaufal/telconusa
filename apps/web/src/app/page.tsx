"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import CSWidget from "@/components/CSWidget";
import { CRM_API, CustomerUser, formatIDR, getCustomerAuth } from "@/lib/auth";

interface Product {
  sku: string;
  name: string;
  business_line: string;
  unit_price: number;
  billing_cycle: string;
  description?: string;
  speed_label?: string;
}

const PERSONAL_FALLBACK: Product[] = [
  { sku: "HOME-20", name: "TelcoHome Fiber 20 Mbps", business_line: "HOME", unit_price: 250000, billing_cycle: "MONTHLY", description: "Internet rumah fiber optik stabil untuk keluarga kecil & belajar online.", speed_label: "20 Mbps" },
  { sku: "HOME-50", name: "TelcoHome Fiber 50 Mbps", business_line: "HOME", unit_price: 400000, billing_cycle: "MONTHLY", description: "Favorit keluarga & WFH — fiber simetris 50 Mbps bebas FUP.", speed_label: "50 Mbps" },
  { sku: "HOME-100", name: "TelcoHome Fiber 100 Mbps", business_line: "HOME", unit_price: 600000, billing_cycle: "MONTHLY", description: "Ultra-fast fiber 100 Mbps untuk gaming kompetitif, 4K, dan smart home.", speed_label: "100 Mbps" },
  { sku: "MOB-PRE-10", name: "Prabayar 5G 10 GB", business_line: "PREPAID", unit_price: 50000, billing_cycle: "ONE_TIME", description: "Kuota 5G ultra cepat 10 GB aktif 30 hari penuh tanpa pembagian jam.", speed_label: "10 GB" },
  { sku: "MOB-PRE-50", name: "Prabayar 5G 50 GB", business_line: "PREPAID", unit_price: 150000, billing_cycle: "ONE_TIME", description: "Kuota besar 50 GB anti ribet untuk streaming, meeting, & hotspot.", speed_label: "50 GB" },
  { sku: "MOB-POST-50", name: "Pascabayar Priority 50 GB", business_line: "POSTPAID", unit_price: 175000, billing_cycle: "MONTHLY", description: "Tagihan bulanan fleksibel dengan prioritas jaringan 5G+ di kota besar.", speed_label: "Priority 5G" },
];

const HERO_SLIDES = [
  {
    badge: "JARINGAN 5G+ NUSANTARA",
    title: "TelcoNusa ULTRA 5G+",
    subtitle: "Kecepatan hingga 1.2 Gbps dengan latensi di bawah 12ms. Streaming 4K, cloud gaming, dan video call tanpa jeda di mana pun Anda melangkah.",
    ctaText: "Pilih Paket 5G+",
    ctaHref: "#produk",
    accentLabel: "1.2 Gbps",
    accentSub: "Peak 5G+ Speed · Latency 11ms",
  },
  {
    badge: "INTERNET RUMAH FIBER OPTIK",
    title: "TelcoHome Fiber Simetris",
    subtitle: "Upload & download sama cepat tanpa FUP. Gratis sewa modem ONT Wi-Fi 6 dan instalasi rapi oleh teknisi bersertifikat dalam 24 jam.",
    ctaText: "Daftar & Pesan Fiber",
    ctaHref: "/order?sku=HOME-50",
    accentLabel: "100 Mbps",
    accentSub: "1:1 Simetris · Tanpa Batas Kuota",
  },
  {
    badge: "PROGRAM REFERRAL RESMI",
    title: "Pasang Lebih Cepat Pakai Referral",
    subtitle: "Punya kode referral dari tim kami? Masukkan saat checkout setelah daftar akun untuk mendapatkan prioritas penjadwalan teknisi.",
    ctaText: "Pesan + Kode Referral",
    ctaHref: "/order?sku=HOME-50&ref=REF-EMP0017",
    accentLabel: "REF-EMP",
    accentSub: "Prioritas Jadwal · Verifikasi Otomatis",
  },
];

const FAQS = [
  {
    q: "Apakah saya harus mendaftar akun sebelum memesan paket?",
    a: "Ya! Pendaftaran atau login akun pelanggan hanya butuh 30 detik agar Anda bisa memantau status order, jadwal kedatangan teknisi, kode alamat pemasangan, nomor Virtual Account Finance, serta mengajukan tiket CS langsung di MyTelcoNusa.",
  },
  {
    q: "Bagaimana cara menghubungi Layanan CS 24/7 TelcoNusa?",
    a: "Anda dapat langsung mengisi formulir Layanan CS 24/7 di bagian Bantuan pada halaman ini, membuka halaman /bantuan, atau mengklik tombol Layanan CS 24/7 di pojok kanan bawah kapan saja tanpa harus login terlebih dahulu.",
  },
  {
    q: "Apakah harga paket sudah termasuk PPN dan perangkat ONT?",
    a: "Harga paket di katalog belum termasuk PPN 11% dan biaya instalasi Rp150.000 (sekali bayar di awal). Modem ONT Wi-Fi 6 dipinjamkan gratis selama masa berlangganan.",
  },
  {
    q: "Bisakah satu pelanggan mendaftarkan lebih dari satu alamat pemasangan?",
    a: "Bisa! Setiap pemesanan layanan internet rumah dapat mencatat alamat pemasangan yang berbeda di bawah satu akun MyTelcoNusa Anda.",
  },
];

function DeviceIllustration({ line }: { line: string }) {
  if (line === "HOME") {
    return (
      <svg viewBox="0 0 120 68" className="w-24 h-14" fill="none">
        <rect x="26" y="34" width="68" height="22" rx="6" fill="#0F172A" />
        <rect x="32" y="42" width="56" height="4" rx="2" fill="#1E293B" />
        <circle cx="40" cy="44" r="2.2" fill="#22C55E" />
        <circle cx="49" cy="44" r="2.2" fill="#FF4757" />
        <circle cx="58" cy="44" r="2.2" fill="#38BDF8" />
        <path d="M40 34L36 14" stroke="#334155" strokeWidth="4" strokeLinecap="round" />
        <path d="M80 34L84 14" stroke="#334155" strokeWidth="4" strokeLinecap="round" />
        <path d="M48 22C54 16 66 16 72 22" stroke="#E11D2E" strokeWidth="3" strokeLinecap="round" />
        <path d="M53 28C57 24 63 24 67 28" stroke="#FF4757" strokeWidth="3" strokeLinecap="round" />
      </svg>
    );
  }
  if (line === "PREPAID") {
    return (
      <svg viewBox="0 0 120 68" className="w-24 h-14" fill="none">
        <rect x="34" y="10" width="52" height="48" rx="8" fill="#E11D2E" />
        <path d="M72 10L86 24V10H72Z" fill="#9F1239" />
        <rect x="44" y="28" width="24" height="18" rx="3" fill="#FDE68A" />
        <path d="M52 28V46M60 28V46M44 37H68" stroke="#D97706" strokeWidth="1.2" />
        <text x="44" y="22" fill="#FFFFFF" fontSize="8" fontWeight="800">5G+</text>
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 120 68" className="w-24 h-14" fill="none">
      <rect x="20" y="12" width="80" height="44" rx="8" fill="#1E293B" />
      <rect x="20" y="12" width="80" height="44" rx="8" stroke="#E11D2E" strokeWidth="1.5" />
      <circle cx="36" cy="34" r="8" fill="#E11D2E" />
      <circle cx="43" cy="27" r="2.5" fill="#FF6B7A" />
      <rect x="54" y="28" width="32" height="4" rx="2" fill="#F8FAFC" />
      <rect x="54" y="36" width="22" height="3" rx="1.5" fill="#94A3B8" />
    </svg>
  );
}

export default function PersonalCustomerLandingPage() {
  const [products, setProducts] = useState<Product[]>(PERSONAL_FALLBACK);
  const [filter, setFilter] = useState<string>("ALL");
  const [slideIdx, setSlideIdx] = useState(0);
  const [customerUser, setCustomerUser] = useState<CustomerUser | null>(null);
  const [customerToken, setCustomerToken] = useState<string | null>(null);

  // Speed Recommender
  const [devices, setDevices] = useState<"1-3" | "4-8" | "9+">("4-8");
  const [activity, setActivity] = useState<"wfh" | "4k" | "gaming">("wfh");

  // Coverage Checker
  const [postalCode, setPostalCode] = useState("40132");
  const [coverageRes, setCoverageRes] = useState<any>(null);
  const [coverageLoading, setCoverageLoading] = useState(false);

  // Inline Layanan CS 24/7 Form
  const [csForm, setCsForm] = useState({
    full_name: "",
    email: "",
    whatsapp_number: "628",
    priority: "P3",
    subject: "",
    description: "",
  });
  const [csLoading, setCsLoading] = useState(false);
  const [csSuccess, setCsSuccess] = useState<{ ticket_code: string; status: string } | null>(null);
  const [csError, setCsError] = useState<string | null>(null);

  // FAQ
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  useEffect(() => {
    const auth = getCustomerAuth();
    if (auth.token && auth.user && auth.user.role === "CUSTOMER") {
      setCustomerToken(auth.token);
      setCustomerUser(auth.user);
    }

    fetch(`${CRM_API}/api/v1/catalog`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data: Product[]) => {
        const personal = data.filter((p) => p.business_line !== "B2B" && !p.sku.startsWith("SVC-"));
        if (personal.length > 0) setProducts(personal);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setSlideIdx((prev) => (prev + 1) % HERO_SLIDES.length);
    }, 6500);
    return () => clearInterval(timer);
  }, []);

  async function checkCoverage(codeToCheck?: string) {
    const target = (codeToCheck ?? postalCode).trim();
    if (!target) return;
    setPostalCode(target);
    setCoverageLoading(true);
    try {
      const r = await fetch(`${CRM_API}/api/v1/coverage?postal_code=${encodeURIComponent(target)}`, { cache: "no-store" });
      if (r.ok) {
        setCoverageRes(await r.json());
      }
    } catch {
      setCoverageRes({
        postal_code: target,
        is_covered: ["12110", "10310", "40132", "40171", "60281", "60115"].includes(target),
        city_name: "Area Layanan",
        district: "-",
      });
    } finally {
      setCoverageLoading(false);
    }
  }

  async function handleInlineCS(e: React.FormEvent) {
    e.preventDefault();
    setCsLoading(true);
    setCsError(null);
    try {
      const isLogged = Boolean(customerToken && customerUser);
      const url = isLogged ? `${CRM_API}/api/v1/tickets` : `${CRM_API}/api/v1/public/support`;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (isLogged && customerToken) headers.Authorization = `Bearer ${customerToken}`;

      const payload = isLogged
        ? { priority: csForm.priority, subject: csForm.subject, description: csForm.description }
        : csForm;

      const r = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const json = await r.json();
      if (!r.ok) throw new Error(json.detail || "Gagal mengirim tiket CS.");
      setCsSuccess({ ticket_code: json.ticket_code, status: json.status });
      setCsForm({ full_name: "", email: "", whatsapp_number: "628", priority: "P3", subject: "", description: "" });
    } catch (err: any) {
      setCsError(err.message || "Gagal terhubung ke layanan CS TelcoNusa.");
    } finally {
      setCsLoading(false);
    }
  }

  const recommendedSku =
    devices === "9+" || activity === "gaming"
      ? { sku: "HOME-100", title: "TelcoHome Fiber 100 Mbps", price: 600000, reason: "Ideal untuk 9+ perangkat bersamaan, upload 4K, dan ping rendah untuk gaming kompetitif." }
      : devices === "4-8" || activity === "4k"
      ? { sku: "HOME-50", title: "TelcoHome Fiber 50 Mbps", price: 400000, reason: "Pilihan terpopuler keluarga! Lancar untuk WFH video conference, Smart TV 4K, dan 4–8 gadget sekaligus." }
      : { sku: "HOME-20", title: "TelcoHome Fiber 20 Mbps", price: 250000, reason: "Hemat & stabil untuk 1–3 perangkat harian, browsing, media sosial, dan meeting online." };

  const slide = HERO_SLIDES[slideIdx];
  const filtered = filter === "ALL" ? products : products.filter((p) => p.business_line === filter);

  return (
    <div className="min-h-screen flex flex-col bg-white text-slate-900">
      {/* 100% Customer-Only Consumer Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-xs">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center shrink-0">
            <img src="/brand/logos/telconusa-orbit-light.svg" alt="TelcoNusa" className="h-9 w-auto" />
          </Link>

          <nav className="hidden lg:flex items-center gap-6 text-sm font-semibold text-slate-600">
            <a href="#produk" onClick={() => setFilter("HOME")} className="hover:text-[#E11D2E] transition">TelcoHome Fiber</a>
            <a href="#produk" onClick={() => setFilter("PREPAID")} className="hover:text-[#E11D2E] transition">Prabayar 5G</a>
            <a href="#produk" onClick={() => setFilter("POSTPAID")} className="hover:text-[#E11D2E] transition">Pascabayar</a>
            <a href="#cakupan" className="hover:text-[#E11D2E] transition">Cek Cakupan</a>
            <a href="#bantuan" className="hover:text-[#E11D2E] transition">Layanan CS 24/7</a>
          </nav>

          <div className="flex items-center gap-2">
            {customerUser ? (
              <>
                <Link
                  href="/portal"
                  className="px-4 py-2 rounded-full border border-slate-200 hover:border-[#E11D2E] text-xs font-bold text-slate-700 hover:text-[#E11D2E] transition"
                >
                  MyTelcoNusa ({customerUser.name.split(" ")[0]})
                </Link>
                <Link
                  href="/order?sku=HOME-50"
                  className="px-5 py-2.5 rounded-full bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold shadow-md shadow-red-600/20 transition"
                >
                  Pesan Paket
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-full border border-slate-200 hover:border-[#E11D2E] text-xs font-bold text-slate-700 hover:text-[#E11D2E] transition"
                >
                  Masuk
                </Link>
                <Link
                  href="/register"
                  className="hidden sm:inline-flex px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 text-xs font-bold text-slate-800 transition"
                >
                  Daftar
                </Link>
                <Link
                  href="/order?sku=HOME-50"
                  className="px-5 py-2.5 rounded-full bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold shadow-md shadow-red-600/20 transition"
                >
                  Berlangganan
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* DYNAMIC 3-SLIDE HERO CAROUSEL */}
      <section className="relative overflow-hidden bg-[#070B14] text-white pb-20 pt-14 md:pt-20 md:pb-28">
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-700"
          style={{
            background:
              "radial-gradient(circle at 78% 30%, rgba(225, 29, 46, 0.36), transparent 52%), radial-gradient(circle at 12% 85%, rgba(159, 18, 57, 0.28), transparent 48%)",
          }}
        />
        <div className="relative max-w-7xl mx-auto px-5 sm:px-6 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 text-[11px] font-bold tracking-widest uppercase text-[#FF8A95]">
              <span className="h-2 w-2 rounded-full bg-[#FF4757] animate-pulse" />
              {slide.badge}
            </div>

            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.08]">
              {slide.title}
            </h1>
            <p className="text-slate-300 text-base sm:text-lg max-w-xl leading-relaxed">
              {slide.subtitle}
            </p>

            <div className="grid grid-cols-3 gap-3 max-w-lg pt-1">
              {[
                { t: "5G TERCEPAT", s: "Up to 1.2 Gbps" },
                { t: "FIBER STABIL", s: "Uptime 99.9%" },
                { t: "BEBAS FUP", s: "Kuota Simetris" },
              ].map((b) => (
                <div key={b.t} className="rounded-xl bg-white/5 border border-white/10 px-3 py-2.5 text-center backdrop-blur-sm">
                  <div className="font-display text-[11px] font-extrabold tracking-wide text-white">★ {b.t}</div>
                  <div className="text-[11px] text-rose-300 mt-0.5">{b.s}</div>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href={slide.ctaHref}
                className="px-7 py-3.5 rounded-full bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm shadow-xl shadow-red-600/30 transition"
              >
                {slide.ctaText}
              </Link>
              <a
                href="#bantuan"
                className="px-6 py-3.5 rounded-full bg-white/10 hover:bg-white/15 border border-white/20 text-white font-semibold text-sm transition"
              >
                Hubungi CS 24/7
              </a>
            </div>
          </div>

          <div className="lg:col-span-5 flex justify-center">
            <div className="w-full max-w-md rounded-3xl bg-gradient-to-br from-slate-900/90 to-rose-950/50 border border-white/15 p-7 shadow-2xl backdrop-blur-md">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-5">
                <span className="font-mono-num uppercase tracking-wider">TelcoNusa Network Telemetry</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">● LIVE</span>
              </div>

              <div className="flex items-center justify-center py-4">
                <svg viewBox="0 0 220 130" className="w-60 h-36" fill="none">
                  <path d="M 30 110 A 80 80 0 0 1 190 110" stroke="#1E293B" strokeWidth="14" strokeLinecap="round" />
                  <path d="M 30 110 A 80 80 0 0 1 178 65" stroke="url(#hero-gauge)" strokeWidth="14" strokeLinecap="round" />
                  <defs>
                    <linearGradient id="hero-gauge" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#9F1239" />
                      <stop offset="60%" stopColor="#E11D2E" />
                      <stop offset="100%" stopColor="#FF6B7A" />
                    </linearGradient>
                  </defs>
                  <text x="110" y="92" textAnchor="middle" fill="#FFFFFF" fontSize="26" fontWeight="800" fontFamily="monospace">
                    {slide.accentLabel}
                  </text>
                  <text x="110" y="114" textAnchor="middle" fill="#FDA4AF" fontSize="9.5" fontWeight="600">
                    {slide.accentSub}
                  </text>
                </svg>
              </div>

              <div className="grid grid-cols-3 gap-2.5 pt-4 border-t border-white/10 text-center text-xs">
                <div>
                  <div className="text-slate-400">Instalasi</div>
                  <div className="font-bold text-white mt-0.5">1×24 Jam</div>
                </div>
                <div>
                  <div className="text-slate-400">Wilayah</div>
                  <div className="font-bold text-white mt-0.5">JKT · BDG · SBY</div>
                </div>
                <div>
                  <div className="text-slate-400">Layanan CS</div>
                  <div className="font-bold text-[#FF6B7A] mt-0.5">24/7 SLA</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="relative max-w-7xl mx-auto px-6 mt-10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {HERO_SLIDES.map((s, idx) => (
              <button
                key={s.title}
                onClick={() => setSlideIdx(idx)}
                aria-label={`Slide ${idx + 1}`}
                className={`h-2 rounded-full transition-all cursor-pointer ${
                  idx === slideIdx ? "w-8 bg-[#FF4757]" : "w-2 bg-white/30 hover:bg-white/60"
                }`}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSlideIdx((slideIdx - 1 + HERO_SLIDES.length) % HERO_SLIDES.length)}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-sm cursor-pointer"
            >
              ←
            </button>
            <button
              onClick={() => setSlideIdx((slideIdx + 1) % HERO_SLIDES.length)}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-sm cursor-pointer"
            >
              →
            </button>
          </div>
        </div>
      </section>

      {/* FLOATING QUICK-ACTION UTILITY BAR */}
      <section className="relative z-20 -mt-10 max-w-6xl w-full mx-auto px-5 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {[
            { title: "Cek Cakupan Fiber", desc: "Cek ketersediaan kode pos", href: "#cakupan", icon: "📍" },
            { title: "Beli Paket Cepat", desc: "Daftar & pilih jadwal", href: "/order?sku=HOME-50", icon: "⚡" },
            { title: "Lacak Pemasangan", desc: "Pantau teknisi MyTelcoNusa", href: "/portal", icon: "🛰️" },
            { title: "Layanan CS 24/7", desc: "Pengaduan & bantuan langsung", href: "#bantuan", icon: "🎧" },
          ].map((item) => (
            <a
              key={item.title}
              href={item.href}
              className="bg-white rounded-2xl border border-slate-200/90 p-4 sm:p-5 shadow-lg shadow-slate-900/5 hover:border-[#E11D2E] hover:-translate-y-0.5 transition flex items-start gap-3.5"
            >
              <span className="w-10 h-10 rounded-xl bg-rose-50 text-lg flex items-center justify-center shrink-0">
                {item.icon}
              </span>
              <div>
                <div className="font-display text-sm font-bold text-slate-900">{item.title}</div>
                <div className="text-xs text-slate-500 mt-0.5">{item.desc}</div>
              </div>
            </a>
          ))}
        </div>
      </section>

      {/* PRODUCT EXPLORER */}
      <section id="produk" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-xs font-bold uppercase tracking-widest text-[#E11D2E]">
              Paket Personal TelcoNusa
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-slate-900 mt-1.5">
              Eksplor produk sesuai kebutuhanmu!
            </h2>
            <p className="text-slate-500 text-sm sm:text-base mt-2">
              Harga jujur dan transparan. Daftar atau masuk dengan akun pelanggan Anda untuk memesan dan memantau instalasi secara real-time.
            </p>

            <div className="flex flex-wrap justify-center gap-2 mt-7">
              {[
                { key: "ALL", label: "Semua Paket" },
                { key: "HOME", label: "TelcoHome Fiber" },
                { key: "PREPAID", label: "Prabayar 5G" },
                { key: "POSTPAID", label: "Pascabayar Priority" },
              ].map((t) => (
                <button
                  key={t.key}
                  onClick={() => setFilter(t.key)}
                  className={`px-4 py-2 rounded-full text-xs sm:text-sm font-bold transition cursor-pointer ${
                    filter === t.key
                      ? "bg-[#E11D2E] text-white shadow-sm"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p) => {
              const isBest = p.sku === "HOME-50";
              return (
                <div
                  key={p.sku}
                  className={`relative rounded-3xl p-6 transition flex flex-col justify-between ${
                    isBest
                      ? "border-2 border-[#E11D2E] bg-gradient-to-b from-rose-50/40 to-white shadow-xl shadow-red-600/10"
                      : "border border-slate-200 bg-white hover:border-slate-300 hover:shadow-lg"
                  }`}
                >
                  {isBest && (
                    <span className="absolute -top-3 left-6 px-3.5 py-1 rounded-full bg-[#E11D2E] text-white text-[11px] font-extrabold tracking-wide shadow">
                      ★ PALING LARIS
                    </span>
                  )}

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <DeviceIllustration line={p.business_line} />
                      <div className="text-right">
                        <span className="inline-block px-2.5 py-1 rounded-lg bg-rose-50 text-[#BE123C] text-[10px] font-bold uppercase tracking-wider">
                          {p.business_line === "HOME" ? "Fiber Rumah" : p.business_line === "PREPAID" ? "Prabayar 5G" : "Pascabayar"}
                        </span>
                        <div className="font-mono-num text-[11px] text-slate-400 mt-1">{p.sku}</div>
                      </div>
                    </div>

                    <h3 className="font-display text-xl font-extrabold text-slate-900">{p.name}</h3>
                    <p className="text-sm text-slate-500 mt-1.5 mb-5">{p.description}</p>

                    <ul className="space-y-2 text-xs text-slate-700 mb-6">
                      {p.business_line === "HOME" ? (
                        <>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Gratis sewa modem ONT Wi-Fi 6</li>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Kecepatan simetris &amp; bebas FUP</li>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Bisa pasang di beberapa alamat</li>
                        </>
                      ) : (
                        <>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Kuota utama 24 jam penuh di jaringan 5G+</li>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Aktivasi instan tanpa potong pulsa tersembunyi</li>
                          <li className="flex items-center gap-2"><span className="text-emerald-600 font-bold">✓</span> Dukungan eSIM &amp; kartu fisik</li>
                        </>
                      )}
                    </ul>
                  </div>

                  <div className="pt-4 border-t border-slate-100">
                    <div className="flex items-end justify-between">
                      <div>
                        <div className="text-[11px] text-slate-400 font-semibold">
                          {p.billing_cycle === "MONTHLY" ? "Biaya per bulan (sebelum PPN 11%)" : "Sekali bayar (sebelum PPN 11%)"}
                        </div>
                        <div className="font-mono-num text-2xl font-extrabold text-[#E11D2E]">
                          {formatIDR(p.unit_price)}
                        </div>
                        {p.business_line === "HOME" && (
                          <div className="text-[11px] text-slate-500">+ Instalasi awal Rp150.000</div>
                        )}
                      </div>
                      <Link
                        href={`/order?sku=${p.sku}`}
                        className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-[#E11D2E] text-white text-xs font-bold transition shrink-0"
                      >
                        Pesan →
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* SPEED RECOMMENDER + LIVE COVERAGE CHECKER */}
      <section id="cakupan" className="py-16 bg-slate-50 border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-3xl border border-slate-200 p-7 shadow-sm">
            <span className="text-[11px] font-bold uppercase tracking-widest text-[#E11D2E]">
              Asisten Pilih Paket
            </span>
            <h3 className="font-display text-2xl font-extrabold text-slate-900 mt-1 mb-5">
              Bingung pilih kecepatan fiber?
            </h3>

            <div className="space-y-4">
              <div>
                <div className="text-xs font-bold text-slate-700 mb-2">1. Jumlah perangkat di rumah</div>
                <div className="grid grid-cols-3 gap-2">
                  {(["1-3", "4-8", "9+"] as const).map((d) => (
                    <button
                      key={d}
                      onClick={() => setDevices(d)}
                      className={`py-2.5 rounded-xl text-xs font-bold border transition cursor-pointer ${
                        devices === d ? "border-[#E11D2E] bg-rose-50 text-[#BE123C]" : "border-slate-200 text-slate-600"
                      }`}
                    >
                      {d} Gadget
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs font-bold text-slate-700 mb-2">2. Aktivitas utama harian</div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { k: "wfh", label: "WFH & Belajar" },
                    { k: "4k", label: "Streaming 4K" },
                    { k: "gaming", label: "Gaming Pro" },
                  ].map((a) => (
                    <button
                      key={a.k}
                      onClick={() => setActivity(a.k as any)}
                      className={`py-2.5 rounded-xl text-xs font-bold border transition cursor-pointer ${
                        activity === a.k ? "border-[#E11D2E] bg-rose-50 text-[#BE123C]" : "border-slate-200 text-slate-600"
                      }`}
                    >
                      {a.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-4 rounded-2xl bg-slate-950 text-white p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] text-rose-300 font-bold uppercase">Rekomendasi Terbaik Untukmu</div>
                  <div className="font-display text-lg font-extrabold mt-0.5">{recommendedSku.title}</div>
                  <p className="text-xs text-slate-300 mt-1">{recommendedSku.reason}</p>
                </div>
                <div className="shrink-0 text-right">
                  <div className="font-mono-num text-lg font-extrabold text-[#FF5C6C]">{formatIDR(recommendedSku.price)}/bln</div>
                  <Link
                    href={`/order?sku=${recommendedSku.sku}`}
                    className="inline-block mt-2 px-4 py-2 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold"
                  >
                    Pilih Paket Ini →
                  </Link>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-slate-200 p-7 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-widest text-[#E11D2E]">
                Live Coverage Checker
              </span>
              <h3 className="font-display text-2xl font-extrabold text-slate-900 mt-1 mb-2">
                Cek cakupan fiber di alamatmu
              </h3>
              <p className="text-sm text-slate-500 mb-5">
                Masukkan kode pos rumah Anda untuk pengecekan jaringan fiber TelcoNusa secara real-time.
              </p>

              <div className="flex gap-2">
                <input
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  placeholder="Masukkan kode pos (mis. 40132)"
                  className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm font-mono-num"
                />
                <button
                  onClick={() => checkCoverage()}
                  disabled={coverageLoading}
                  className="px-6 py-3 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white text-xs font-bold cursor-pointer"
                >
                  {coverageLoading ? "Mengecek..." : "Cek Area"}
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5 mt-3 text-[11px]">
                <span className="text-slate-400 py-1">Contoh cepat:</span>
                {[
                  { code: "12110", label: "12110 (Jaksel)" },
                  { code: "40132", label: "40132 (Bandung)" },
                  { code: "60281", label: "60281 (Surabaya)" },
                  { code: "99999", label: "99999 (Luar Area)" },
                ].map((s) => (
                  <button
                    key={s.code}
                    onClick={() => checkCoverage(s.code)}
                    className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 hover:text-[#BE123C] font-mono-num font-semibold text-slate-600 cursor-pointer"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {coverageRes && (
              <div
                className={`mt-5 rounded-2xl p-4 border text-sm ${
                  coverageRes.is_covered
                    ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                    : "bg-amber-50 border-amber-200 text-amber-900"
                }`}
              >
                {coverageRes.is_covered ? (
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-bold">✓ Area Terjangkau Fiber TelcoNusa!</div>
                      <div className="text-xs mt-0.5">
                        Kode Pos <span className="font-mono-num font-bold">{coverageRes.postal_code}</span> ·{" "}
                        {coverageRes.district}, {coverageRes.city_name} ({coverageRes.city_code})
                      </div>
                    </div>
                    <Link href="/order?sku=HOME-50" className="px-3.5 py-2 rounded-lg bg-emerald-700 text-white text-xs font-bold shrink-0">
                      Pasang →
                    </Link>
                  </div>
                ) : (
                  <div>
                    <div className="font-bold">Area belum masuk cakupan fiber</div>
                    <div className="text-xs mt-0.5">
                      Kode pos <span className="font-mono-num font-bold">{coverageRes.postal_code}</span> belum tersedia untuk TelcoHome Fiber, namun Anda tetap dapat menggunakan layanan <strong>Prabayar 5G</strong> atau menghubungi CS kami.
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* REFERRAL & CAMPAIGN BANNER */}
      <section id="referral" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6">
          <div className="rounded-3xl bg-gradient-to-r from-[#0F172A] via-[#88131D] to-[#E11D2E] text-white p-8 md:p-12 flex flex-col lg:flex-row items-center justify-between gap-8 shadow-xl">
            <div className="max-w-2xl">
              <span className="px-3 py-1 rounded-full bg-white/15 text-[11px] font-bold uppercase tracking-wider">
                Campaign Promo Nusantara · CMP-2026-001
              </span>
              <h3 className="font-display text-2xl sm:text-3xl font-extrabold mt-3">
                Punya Kode Referral dari Tim Marketing TelcoNusa?
              </h3>
              <p className="text-rose-100 text-sm sm:text-base mt-2">
                Gunakan kode referral (contoh: <code className="font-mono-num bg-black/30 px-2 py-0.5 rounded font-bold">REF-EMP0017</code>) saat pemesanan untuk mendapatkan pendampingan aktivasi prioritas.
              </p>
            </div>
            <Link
              href="/order?sku=HOME-50&ref=REF-EMP0017"
              className="px-7 py-4 rounded-full bg-white text-[#9F1239] hover:bg-rose-50 font-display font-extrabold text-sm shadow-lg shrink-0 transition"
            >
              Gunakan Kode Referral →
            </Link>
          </div>
        </div>
      </section>

      {/* DEDICATED LAYANAN CS 24/7 SECTION */}
      <section id="bantuan" className="py-16 bg-slate-950 text-white">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-5 space-y-5">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 text-[#FF8A95] text-xs font-bold uppercase tracking-wider">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Layanan CS TelcoNusa 24/7
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold leading-tight">
              Butuh bantuan cepat? Tim CS kami siap 24 jam.
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Laporkan gangguan jaringan, tanyakan cakupan pemasangan rumah, atau konfirmasi tagihan Anda. Setiap laporan langsung tercatat dengan nomor tiket resmi di pusat layanan pelanggan kami.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {[
                { title: "SLA Gangguan P1/P2", desc: "Respons teknisi & tim CS prioritas < 15 menit" },
                { title: "Bantuan Pemasangan", desc: "Cek kesiapan tiang ODP & jadwal survey rumah" },
                { title: "Administrasi & VA", desc: "Bantuan faktur PPN & verifikasi pembayaran" },
                { title: "Live Status Tiket", desc: "Pantau progres penanganan di MyTelcoNusa" },
              ].map((card) => (
                <div key={card.title} className="rounded-2xl bg-white/5 border border-white/10 p-4">
                  <div className="font-display font-bold text-xs text-[#FF8A95]">{card.title}</div>
                  <div className="text-xs text-slate-300 mt-1">{card.desc}</div>
                </div>
              ))}
            </div>

            <div className="pt-2">
              <Link
                href="/bantuan"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-full bg-white/10 hover:bg-white/20 border border-white/15 text-xs font-bold transition"
              >
                Buka Halaman Pusat Bantuan Lengkap →
              </Link>
            </div>
          </div>

          <div className="lg:col-span-7 bg-white text-slate-900 rounded-3xl p-6 sm:p-8 shadow-2xl">
            <div className="flex items-center justify-between gap-3 mb-5">
              <div>
                <h3 className="font-display text-xl font-extrabold">Buat Tiket Layanan CS 24/7</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Langsung terhubung ke antrean Customer Service TelcoNusa
                </p>
              </div>
              {customerUser && (
                <span className="px-3 py-1 rounded-full bg-rose-50 text-[#BE123C] text-[11px] font-bold">
                  {customerUser.code} · {customerUser.name}
                </span>
              )}
            </div>

            {csSuccess ? (
              <div className="rounded-2xl bg-emerald-50 border border-emerald-200 p-6 space-y-3">
                <div className="font-display text-lg font-extrabold text-emerald-900">
                  ✓ Tiket Layanan CS Berhasil Dibuat!
                </div>
                <p className="text-sm text-emerald-800">
                  Nomor Tiket: <strong className="font-mono-num">{csSuccess.ticket_code}</strong> · Status:{" "}
                  <strong className="font-mono-num">{csSuccess.status}</strong>. Tim CS kami sedang meninjau permintaan Anda.
                </p>
                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setCsSuccess(null)}
                    className="px-4 py-2 rounded-xl bg-emerald-700 text-white text-xs font-bold cursor-pointer"
                  >
                    Kirim Pertanyaan / Keluhan Lain
                  </button>
                  <Link href="/portal" className="px-4 py-2 rounded-xl border border-emerald-300 bg-white text-emerald-900 text-xs font-bold">
                    Pantau di MyTelcoNusa →
                  </Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleInlineCS} className="space-y-4">
                {!customerUser && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Nama Lengkap</label>
                      <input
                        required
                        value={csForm.full_name}
                        onChange={(e) => setCsForm({ ...csForm, full_name: e.target.value })}
                        placeholder="Nama Anda"
                        className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Email Aktif</label>
                      <input
                        required
                        type="email"
                        value={csForm.email}
                        onChange={(e) => setCsForm({ ...csForm, email: e.target.value })}
                        placeholder="nama@email.com"
                        className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">No. WhatsApp</label>
                      <input
                        value={csForm.whatsapp_number}
                        onChange={(e) => setCsForm({ ...csForm, whatsapp_number: e.target.value })}
                        placeholder="62812..."
                        className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm font-mono-num"
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Prioritas</label>
                    <select
                      value={csForm.priority}
                      onChange={(e) => setCsForm({ ...csForm, priority: e.target.value })}
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    >
                      <option value="P1">P1 — Darurat / LOS Merah</option>
                      <option value="P2">P2 — Koneksi Putus</option>
                      <option value="P3">P3 — Tanya Paket / Lambat</option>
                      <option value="P4">P4 — Tagihan &amp; VA</option>
                    </select>
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-bold text-slate-700 mb-1">Subjek Bantuan</label>
                    <input
                      required
                      value={csForm.subject}
                      onChange={(e) => setCsForm({ ...csForm, subject: e.target.value })}
                      placeholder="Contoh: Tanya jadwal instalasi atau lapor kendala sinyal"
                      className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Detail Kendala / Pertanyaan</label>
                  <textarea
                    required
                    rows={3}
                    value={csForm.description}
                    onChange={(e) => setCsForm({ ...csForm, description: e.target.value })}
                    placeholder="Jelaskan alamat, kendala koneksi, atau pertanyaan layanan Anda..."
                    className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm"
                  />
                </div>

                {csError && (
                  <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs p-3">
                    {csError}
                  </div>
                )}

                <button
                  disabled={csLoading}
                  type="submit"
                  className="w-full py-3.5 rounded-xl bg-[#E11D2E] hover:bg-[#BE123C] text-white font-display font-bold text-sm cursor-pointer disabled:opacity-50"
                >
                  {csLoading ? "Mengirim ke Layanan CS..." : "Kirim ke Layanan CS 24/7 →"}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* TRUST STATS + FAQ */}
      <section className="py-16 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 space-y-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 text-center">
            {[
              { num: "99.9%", label: "Uptime Jaringan Fiber" },
              { num: "< 12ms", label: "Latensi Rata-rata 5G+" },
              { num: "1×24 Jam", label: "Target Pemasangan Rumah" },
              { num: "4.9 / 5", label: "Rating Teknisi dari Pelanggan" },
            ].map((st) => (
              <div key={st.label} className="bg-white rounded-2xl border border-slate-200 p-5">
                <div className="font-display text-3xl font-extrabold text-[#E11D2E]">{st.num}</div>
                <div className="text-xs font-medium text-slate-600 mt-1">{st.label}</div>
              </div>
            ))}
          </div>

          <div className="max-w-3xl mx-auto">
            <h3 className="font-display text-2xl font-extrabold text-center text-slate-900 mb-6">
              Pertanyaan yang Sering Diajukan
            </h3>
            <div className="space-y-3">
              {FAQS.map((f, idx) => {
                const open = openFaq === idx;
                return (
                  <div key={f.q} className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
                    <button
                      onClick={() => setOpenFaq(open ? null : idx)}
                      className="w-full px-5 py-4 text-left flex items-center justify-between gap-4 font-display font-bold text-sm text-slate-900 cursor-pointer"
                    >
                      <span>{f.q}</span>
                      <span className="text-[#E11D2E] text-lg">{open ? "−" : "+"}</span>
                    </button>
                    {open && <div className="px-5 pb-4 text-sm text-slate-600">{f.a}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* 100% Consumer-Only Footer (Zero employee/internal division links) */}
      <footer className="bg-[#070B14] text-slate-400 pt-14 pb-8 mt-auto">
        <div className="max-w-7xl mx-auto px-5 sm:px-6 grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-white/10">
          <div>
            <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-9 w-auto mb-3" />
            <p className="text-xs leading-relaxed">
              PT TelkoNusa Digital — Penyedia layanan konektivitas 5G+ dan TelcoHome Fiber untuk keluarga Indonesia.
            </p>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-white mb-3">Layanan Personal</div>
            <ul className="space-y-2 text-xs">
              <li><a href="#produk" className="hover:text-white">TelcoHome Fiber 20–100 Mbps</a></li>
              <li><a href="#produk" className="hover:text-white">Prabayar 5G</a></li>
              <li><a href="#produk" className="hover:text-white">Pascabayar Priority</a></li>
            </ul>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-white mb-3">Akun &amp; Pemesanan</div>
            <ul className="space-y-2 text-xs">
              <li><Link href="/register" className="hover:text-white">Daftar Akun Pelanggan</Link></li>
              <li><Link href="/login" className="hover:text-white">Masuk Pelanggan</Link></li>
              <li><Link href="/portal" className="hover:text-white">MyTelcoNusa</Link></li>
              <li><Link href="/order" className="hover:text-white">Pesan Paket Baru</Link></li>
            </ul>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-white mb-3">Layanan CS 24/7</div>
            <ul className="space-y-2 text-xs">
              <li><Link href="/bantuan" className="hover:text-white">Pusat Bantuan &amp; Tiket CS</Link></li>
              <li>Area Layanan: Jakarta · Bandung · Surabaya</li>
              <li className="text-slate-500">care@telconusa.id · SLA 24/7</li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-5 sm:px-6 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <span>© 2026 PT TelkoNusa Digital. Seluruh layanan pelanggan dilindungi SLA resmi TelcoNusa.</span>
          <span className="text-slate-500">Connecting Nusantara · Jaringan 5G+ &amp; Fiber Optik</span>
        </div>
      </footer>

      <CSWidget />
    </div>
  );
}

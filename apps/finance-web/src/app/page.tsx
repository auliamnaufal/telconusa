"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FINANCE_API, FINANCE_ROLES, buildEmployeeSsoUrl, clearAuth, formatIDR, getAuth } from "@/lib/auth";

type FinModule = "overview" | "ar" | "ap" | "gl" | "budget";

export default function FinanceAccountingSuitePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState<FinModule>("overview");
  const [expandedJe, setExpandedJe] = useState<string | null>("JE-000001");
  const [msg, setMsg] = useState<string | null>(null);

  // Budget simulator
  const [simCC, setSimCC] = useState("CC-SCM");
  const [simAmount, setSimAmount] = useState(15000000);
  const [simResult, setSimResult] = useState<any>(null);

  async function loadSummary(t: string) {
    const res = await fetch(`${FINANCE_API}/api/v1/dashboard/summary`, {
      headers: { Authorization: `Bearer ${t}` },
      cache: "no-store",
    });
    if (res.status === 401 || res.status === 403) {
      clearAuth();
      router.replace("/login");
      return;
    }
    if (res.ok) setData(await res.json());
  }

  useEffect(() => {
    const { token: t, user: u } = getAuth();
    if (!t || !u || !FINANCE_ROLES.includes(u.role)) {
      router.replace("/login");
      return;
    }
    setToken(t);
    setUser(u);
    loadSummary(t);
  }, []);

  async function simulatePay(invoiceNo: string) {
    if (!token) return;
    const res = await fetch(`${FINANCE_API}/api/v1/invoices/${invoiceNo}/pay`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setMsg(`Pembayaran VA ${invoiceNo} terverifikasi! Jurnal AR-PAY & insentif COM-FIN (10%) terposting otomatis.`);
      loadSummary(token);
    }
  }

  async function payVendorBill(billNo: string) {
    if (!token) return;
    const res = await fetch(`${FINANCE_API}/api/v1/vendor-bills/${billNo}/pay`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setMsg(`Tagihan vendor ${billNo} dibayar! Jurnal AP-PAY terposting & event vendor.paid dikirim ke SCM.`);
      loadSummary(token);
    }
  }

  async function togglePeriod(periodCode: string) {
    if (!token) return;
    const res = await fetch(`${FINANCE_API}/api/v1/periods/${periodCode}/toggle`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const json = await res.json();
      setMsg(`Periode fiskal ${json.period_code} diubah menjadi ${json.status}.`);
      loadSummary(token);
    }
  }

  async function checkBudgetSim(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${FINANCE_API}/api/v1/budgets/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cost_center_code: simCC, amount: simAmount }),
    });
    if (res.ok) setSimResult(await res.json());
  }

  return (
    <div className="min-h-screen flex bg-[#F7F8FA] text-slate-900">
      {/* Deep Obsidian Accounting Sidebar */}
      <aside className="w-64 shrink-0 bg-[#090D16] text-slate-200 flex flex-col border-r border-slate-800">
        <div className="p-5 border-b border-slate-800">
          <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-8 w-auto" />
          <div className="mt-2.5 text-[10px] font-mono-num uppercase tracking-widest text-rose-400 font-bold">
            Finance Accounting Suite · :3004
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {[
            { id: "overview", label: "Ringkasan & Laporan" },
            { id: "ar", label: "Piutang (AR) & VA" },
            { id: "ap", label: "Utang (AP) & 3-Way Match" },
            { id: "gl", label: "Buku Besar (GL) & Periode" },
            { id: "budget", label: "Anggaran & Cost Center" },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setTab(m.id as FinModule)}
              className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                tab === m.id ? "bg-[#E11D2E] text-white" : "text-slate-300 hover:bg-slate-900 hover:text-white"
              }`}
            >
              {m.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 space-y-2">
          <a href={buildEmployeeSsoUrl(token)} className="block w-full text-center py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-white">
            👤 Portal Karyawan Saya
          </a>
          <button onClick={() => { clearAuth(); router.push("/login"); }} className="block w-full py-1.5 text-xs text-slate-400 hover:text-white cursor-pointer">
            Keluar Akun
          </button>
        </div>
      </aside>

      {/* Main Ledger Canvas */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-xl font-extrabold text-slate-900">Sistem Informasi Keuangan (Kelompok 3)</h1>
            <p className="text-xs text-slate-500">Pelaku: <strong>{user?.name}</strong> ({user?.role}) · Dasar Akrual · PPN 11%</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full font-mono-num text-xs font-bold ${data?.kpis.trial_balance_balanced ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700"}`}>
              {data?.kpis.trial_balance_balanced ? "✓ NERACA SALDO SEIMBANG (SELISIH Rp0)" : "MEMUAT..."}
            </span>
          </div>
        </header>

        <main className="p-8 max-w-7xl w-full mx-auto space-y-6">
          {msg && <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800">{msg}</div>}

          {/* Audit-Grade KPI Strip */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            {[
              { label: "Kas & Bank (1100)", val: data ? formatIDR(data.kpis.cash_balance_idr) : "-" },
              { label: "Total Pendapatan", val: data ? formatIDR(data.kpis.total_revenue_idr) : "-" },
              { label: "Total Beban & HPP", val: data ? formatIDR(data.kpis.total_expense_idr) : "-" },
              { label: "Laba Bersih", val: data ? formatIDR(data.kpis.net_profit_idr) : "-" },
              { label: "Piutang (AR)", val: data ? formatIDR(data.kpis.outstanding_ar_idr) : "-" },
              { label: "Utang Vendor (AP)", val: data ? formatIDR(data.kpis.outstanding_ap_idr) : "-" },
            ].map((k) => (
              <div key={k.label} className="bg-white rounded-xl border border-slate-200 p-3.5">
                <div className="text-[11px] font-semibold text-slate-500">{k.label}</div>
                <div className="font-mono-num text-base font-extrabold text-slate-900 mt-1">{k.val}</div>
              </div>
            ))}
          </div>

          {tab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Income Statement Summary */}
              <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 p-6 space-y-3 h-fit">
                <h2 className="font-display font-extrabold text-sm border-b border-slate-100 pb-2">Ringkasan Laba Rugi (SAK)</h2>
                <div className="flex justify-between text-xs"><span>Pendapatan Usaha</span><span className="font-mono-num font-bold text-emerald-700">{data ? formatIDR(data.kpis.total_revenue_idr) : "-"}</span></div>
                <div className="flex justify-between text-xs"><span>Beban Komisi, Penyusutan &amp; Ops</span><span className="font-mono-num font-bold text-red-600">-{data ? formatIDR(data.kpis.total_expense_idr) : "-"}</span></div>
                <div className="flex justify-between text-sm font-extrabold pt-3 border-t border-slate-200">
                  <span>Laba Periode Berjalan</span>
                  <span className="font-mono-num text-[#E11D2E]">{data ? formatIDR(data.kpis.net_profit_idr) : "-"}</span>
                </div>
              </div>

              {/* Full Trial Balance */}
              <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
                  <h2 className="font-display font-bold text-sm">Neraca Saldo (Trial Balance)</h2>
                  {data?.trial_balance && (
                    <span className="font-mono-num text-xs font-bold text-emerald-700">
                      Debit = Kredit = {formatIDR(data.trial_balance.total_debit)}
                    </span>
                  )}
                </div>
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase">
                    <tr>
                      <th className="p-3 text-left">Kode</th>
                      <th className="p-3 text-left">Nama Akun</th>
                      <th className="p-3 text-left">Tipe</th>
                      <th className="p-3 text-right">Debit</th>
                      <th className="p-3 text-right">Kredit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.trial_balance?.accounts || []).map((a: any) => (
                      <tr key={a.account_code} className="border-t border-slate-100">
                        <td className="p-3 font-mono-num font-bold">{a.account_code}</td>
                        <td className="p-3">{a.account_name}</td>
                        <td className="p-3 text-[10px] font-mono-num text-slate-500">{a.account_type}</td>
                        <td className="p-3 text-right font-mono-num">{a.debit ? formatIDR(a.debit) : "-"}</td>
                        <td className="p-3 text-right font-mono-num">{a.credit ? formatIDR(a.credit) : "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                  {data?.trial_balance && (
                    <tfoot className="bg-slate-900 text-white font-mono-num font-bold">
                      <tr>
                        <td colSpan={3} className="p-3 text-right">TOTAL NERACA SALDO</td>
                        <td className="p-3 text-right">{formatIDR(data.trial_balance.total_debit)}</td>
                        <td className="p-3 text-right">{formatIDR(data.trial_balance.total_credit)}</td>
                      </tr>
                    </tfoot>
                  )}
                </table>
              </div>
            </div>
          )}

          {tab === "ar" && (
            <div className="space-y-6">
              {/* Aging Buckets */}
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                {(data?.aging_buckets || []).map((ag: any) => (
                  <div key={ag.bucket} className="bg-white rounded-xl border border-slate-200 p-3.5">
                    <div className="text-[11px] font-bold text-slate-500">{ag.bucket}</div>
                    <div className="font-mono-num text-sm font-extrabold mt-1">{formatIDR(ag.amount)}</div>
                  </div>
                ))}
              </div>

              {/* Invoices Ledger */}
              <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
                <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">Daftar Invoice Pelanggan (AR) &amp; Verifikasi Virtual Account</div>
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500 uppercase">
                    <tr>
                      <th className="p-3 text-left">Invoice</th>
                      <th className="p-3 text-left">Order</th>
                      <th className="p-3 text-left">Pelanggan</th>
                      <th className="p-3 text-left">VA</th>
                      <th className="p-3 text-right">DPP</th>
                      <th className="p-3 text-right">PPN 11%</th>
                      <th className="p-3 text-right">Total</th>
                      <th className="p-3 text-left">Status</th>
                      <th className="p-3 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data?.invoices || []).map((inv: any) => (
                      <tr key={inv.invoice_no} className="border-t border-slate-100">
                        <td className="p-3 font-mono-num font-bold">{inv.invoice_no}</td>
                        <td className="p-3 font-mono-num">{inv.order_no}</td>
                        <td className="p-3">{inv.customer_name}</td>
                        <td className="p-3 font-mono-num">{inv.virtual_account}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(inv.subtotal)}</td>
                        <td className="p-3 text-right font-mono-num">{formatIDR(inv.tax_amount)}</td>
                        <td className="p-3 text-right font-mono-num font-bold">{formatIDR(inv.total)}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded-full font-bold ${inv.status === "PAID" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          {inv.status !== "PAID" ? (
                            <button onClick={() => simulatePay(inv.invoice_no)} className="px-3 py-1.5 rounded-lg bg-[#E11D2E] text-white font-bold cursor-pointer">
                              Verifikasi Bayar VA
                            </button>
                          ) : (
                            <span className="text-slate-400">Lunas</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "ap" && (
            <div className="bg-white rounded-2xl border border-slate-200 overflow-x-auto">
              <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">Tagihan Vendor (AP) &amp; Three-Way Match (Toleransi 2%)</div>
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase">
                  <tr>
                    <th className="p-3 text-left">Bill No.</th>
                    <th className="p-3 text-left">PO Ref</th>
                    <th className="p-3 text-left">Vendor</th>
                    <th className="p-3 text-right">Subtotal</th>
                    <th className="p-3 text-right">PPN</th>
                    <th className="p-3 text-right">Total</th>
                    <th className="p-3 text-left">3-Way Match</th>
                    <th className="p-3 text-left">Status</th>
                    <th className="p-3 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.vendor_bills || []).map((b: any) => (
                    <tr key={b.bill_no} className="border-t border-slate-100">
                      <td className="p-3 font-mono-num font-bold">{b.bill_no}</td>
                      <td className="p-3 font-mono-num">{b.po_no}</td>
                      <td className="p-3 font-mono-num">{b.vendor_code}</td>
                      <td className="p-3 text-right font-mono-num">{formatIDR(b.subtotal)}</td>
                      <td className="p-3 text-right font-mono-num">{formatIDR(b.tax_amount)}</td>
                      <td className="p-3 text-right font-mono-num font-bold">{formatIDR(b.total)}</td>
                      <td className="p-3"><span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold">{b.match_status}</span></td>
                      <td className="p-3 font-bold">{b.status}</td>
                      <td className="p-3 text-right">
                        {b.status !== "PAID" ? (
                          <button onClick={() => payVendorBill(b.bill_no)} className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-[#E11D2E] text-white font-bold cursor-pointer">
                            Bayar Vendor (AP-PAY)
                          </button>
                        ) : (
                          <span className="text-slate-400">Terbayar</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "gl" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Expandable Journal Entries Drill-Down */}
              <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3.5 border-b border-slate-200 font-display font-bold text-sm">
                  Buku Besar &amp; Jurnal Otomatis (Klik baris untuk drill-down Debit/Kredit)
                </div>
                <div className="divide-y divide-slate-100">
                  {(data?.journals || []).map((j: any) => {
                    const isOpen = expandedJe === j.journal_no;
                    return (
                      <div key={j.journal_no} className="p-4">
                        <button
                          onClick={() => setExpandedJe(isOpen ? null : j.journal_no)}
                          className="w-full text-left flex items-center justify-between gap-3 cursor-pointer"
                        >
                          <div>
                            <div className="font-mono-num text-xs font-bold">
                              {j.journal_no} · <span className="text-[#E11D2E]">{j.rule_code}</span> ·{" "}
                              <span className="text-slate-400">Sumber: {j.source_type} ({j.source_id})</span>
                            </div>
                            <div className="text-xs text-slate-600 mt-0.5">{j.description}</div>
                          </div>
                          <span className="text-xs font-mono-num font-bold text-emerald-700">{j.status} {isOpen ? "▲" : "▼"}</span>
                        </button>

                        {isOpen && (
                          <table className="w-full text-xs mt-3 bg-slate-50 rounded-lg overflow-hidden">
                            <thead className="text-slate-500">
                              <tr>
                                <th className="p-2 text-left">Akun</th>
                                <th className="p-2 text-right">Debit</th>
                                <th className="p-2 text-right">Kredit</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(j.lines || []).map((ln: any, idx: number) => (
                                <tr key={idx} className="border-t border-slate-200/60">
                                  <td className="p-2"><span className="font-mono-num font-bold">{ln.account_code}</span> {ln.account_name}</td>
                                  <td className="p-2 text-right font-mono-num">{ln.debit ? formatIDR(ln.debit) : "-"}</td>
                                  <td className="p-2 text-right font-mono-num">{ln.credit ? formatIDR(ln.credit) : "-"}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Fiscal Period Locks */}
              <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 p-5 h-fit space-y-3">
                <h2 className="font-display font-bold text-sm">Kontrol Periode Fiskal</h2>
                <p className="text-xs text-slate-500">Periode LOCKED otomatis menolak posting jurnal baru (NFR-07 &amp; TC-14).</p>
                {(data?.fiscal_periods || []).map((fp: any) => (
                  <div key={fp.period_code} className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-mono-num font-bold">{fp.period_code}</span>
                      <span className={`ml-2 px-2 py-0.5 rounded font-bold text-[10px] ${fp.status === "LOCKED" ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>
                        {fp.status}
                      </span>
                    </div>
                    <button onClick={() => togglePeriod(fp.period_code)} className="px-2.5 py-1 rounded border border-slate-300 font-bold cursor-pointer">
                      {fp.status === "LOCKED" ? "Buka" : "Kunci"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "budget" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
                <h2 className="font-display font-bold text-sm">Serapan Anggaran per Cost Center (2026)</h2>
                {(data?.budgets || []).map((b: any) => {
                  const used = b.committed_amount + b.realized_amount;
                  const pct = Math.min(100, Math.round((used / Math.max(1, b.allocated_amount)) * 100));
                  return (
                    <div key={b.cost_center_code} className="space-y-1.5 text-xs">
                      <div className="flex justify-between font-bold">
                        <span className="font-mono-num">{b.cost_center_code}</span>
                        <span className="font-mono-num">{formatIDR(used)} / {formatIDR(b.allocated_amount)} ({pct}%)</span>
                      </div>
                      <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-[#E11D2E]" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 space-y-4 h-fit">
                <h2 className="font-display font-bold text-sm">Simulator API Cek Anggaran (Dipakai SCM &amp; HRM)</h2>
                <form onSubmit={checkBudgetSim} className="space-y-3">
                  <select value={simCC} onChange={(e) => setSimCC(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs">
                    <option value="CC-SCM">CC-SCM (Pengadaan Barang)</option>
                    <option value="CC-OPS">CC-OPS (Operasional &amp; Teknisi)</option>
                    <option value="CC-SALES">CC-SALES (Komisi &amp; Marketing)</option>
                    <option value="CC-HR">CC-HR (Rekrutmen &amp; SDM)</option>
                  </select>
                  <input type="number" value={simAmount} onChange={(e) => setSimAmount(Number(e.target.value))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono-num" />
                  <button type="submit" className="w-full py-2.5 rounded-lg bg-slate-900 hover:bg-[#E11D2E] text-white text-xs font-bold cursor-pointer">
                    Uji POST /api/v1/budgets/check
                  </button>
                </form>
                {simResult && (
                  <div className={`p-3 rounded-xl text-xs font-mono-num ${simResult.approved ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"}`}>
                    approved: <strong>{String(simResult.approved)}</strong> · Sisa: {formatIDR(simResult.remaining)}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

const TONES: Record<string, string> = {
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
  blue: "bg-sky-50 text-sky-700 border-sky-200",
  red: "bg-rose-50 text-rose-700 border-rose-200",
  slate: "bg-slate-100 text-slate-700 border-slate-200",
};

// Nilai status baku dari contracts/variable_standards.md dan spec bagian 5; jangan membuat status baru.
const STATUS_TONE: Record<string, keyof typeof TONES> = {
  READY_TO_ISSUE: "green", APPROVED: "green", IN_STOCK: "green", RECEIVED: "green", BUDGET_OK: "green", INSTALLED: "green", RETURNED: "green", POSTED: "green",
  REQUESTED: "amber", PENDING_STOCK: "amber", PENDING_APPROVAL: "amber", PENDING_BUDGET: "amber", RESERVED: "amber", PARTIALLY_RECEIVED: "amber", IN_TRANSIT: "amber",
  ISSUED: "blue", WITH_TECHNICIAN: "blue", PO_CREATED: "blue", DRAFT: "blue", CLOSED: "blue",
  FAULTY: "red", LOST: "red", WRITTEN_OFF: "red", REJECTED: "red", CANCELLED: "red", BUDGET_REJECTED: "red",
};

export function StatusBadge({ status }: { status: string }) {
  const tone = TONES[STATUS_TONE[status] ?? "slate"];
  return (
    <span className={`inline-block rounded-md border px-2 py-0.5 font-mono-num text-[11px] font-semibold ${tone}`}>{status}</span>
  );
}

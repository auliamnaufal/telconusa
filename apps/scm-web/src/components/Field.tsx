import type { ReactNode } from "react";

interface Props {
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
}

export function Field({ label, hint, error, children }: Props) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-semibold text-slate-700">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-rose-600">{error}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[#E11D2E] focus:outline-none";

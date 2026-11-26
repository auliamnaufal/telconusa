"use client";

import type { ReactNode } from "react";
import { Button } from "@/components/Button";

interface Props {
  title: string;
  submitLabel: string;
  danger?: boolean;
  loading: boolean;
  disabled?: boolean;
  onSubmit: () => void;
  onClose: () => void;
  children: ReactNode;
}

export function ActionModal({ title, submitLabel, danger = false, loading, disabled = false, onSubmit, onClose, children }: Props) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/50 p-4" role="dialog" aria-modal="true" aria-label={title}>
      <form
        className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <h2 className="font-display text-lg font-bold text-slate-900">{title}</h2>
        <div className="mt-4 space-y-4">{children}</div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Batal
          </Button>
          <button
            type="submit"
            disabled={loading || disabled}
            className={`inline-flex items-center justify-center rounded-lg px-3.5 py-2 text-sm font-semibold text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
              danger ? "bg-rose-700 hover:bg-rose-800" : "bg-[#E11D2E] hover:bg-[#BE123C]"
            }`}
          >
            {loading ? "Memproses..." : submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
}

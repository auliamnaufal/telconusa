"use client";

import type { ReactNode } from "react";
import { Button } from "@/components/Button";

interface Props {
  title: string;
  submitLabel: string;
  loading: boolean;
  onSubmit: () => void;
  onClose: () => void;
  children: ReactNode;
}

export function FormModal({ title, submitLabel, loading, onSubmit, onClose, children }: Props) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/50 p-4" role="dialog" aria-modal="true" aria-label={title}>
      <form
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
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
            disabled={loading}
            className="inline-flex items-center justify-center rounded-lg bg-[#E11D2E] px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#BE123C] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Memproses..." : submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
}

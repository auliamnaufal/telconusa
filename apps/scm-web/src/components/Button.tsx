"use client";

import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

const STYLES: Record<Variant, string> = {
  primary: "bg-[#E11D2E] hover:bg-[#BE123C] text-white",
  secondary: "bg-white hover:bg-slate-50 text-slate-800 border border-slate-300",
  danger: "bg-rose-700 hover:bg-rose-800 text-white",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({ variant = "primary", loading = false, disabled, className = "", children, ...rest }: Props) {
  return (
    <button
      type="button"
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${STYLES[variant]} ${className}`}
    >
      {loading ? "Memproses..." : children}
    </button>
  );
}

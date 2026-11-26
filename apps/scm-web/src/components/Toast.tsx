"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { ApiError } from "@/lib/api";

type Kind = "success" | "error";
interface ToastItem {
  id: number;
  kind: Kind;
  message: string;
}

interface ToastApi {
  success: (message: string) => void;
  // Menampilkan `error.message` dari API apa adanya (kode seperti INSUFFICIENT_STOCK tidak disamarkan).
  error: (error: unknown) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const push = useCallback((kind: Kind, message: string) => {
    const id = Date.now() + Math.random();
    setItems((current) => [...current, { id, kind, message }]);
    setTimeout(() => setItems((current) => current.filter((item) => item.id !== id)), 6000);
  }, []);

  const api = useMemo<ToastApi>(
    () => ({
      success: (message) => push("success", message),
      error: (error) => {
        if (error instanceof ApiError) push("error", `${error.message} (${error.code})`);
        else push("error", error instanceof Error ? error.message : "Terjadi kesalahan");
      },
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {items.map((item) => (
          <div
            key={item.id}
            role="status"
            className={`rounded-lg border px-4 py-3 text-sm shadow-lg ${
              item.kind === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"
            }`}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast harus dipakai di dalam ToastProvider");
  return context;
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ToastProvider } from "@/components/Toast";
import { SCM_ROLES, clearAuth, getAuth, type AuthUser } from "@/lib/auth";
import { canAccess, homeFor, isActive, navFor } from "@/lib/roles";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const { token, user: stored } = getAuth();
    if (!token || !stored || !SCM_ROLES.includes(stored.role)) {
      clearAuth();
      router.replace("/login");
      return;
    }
    setUser(stored);
    if (!canAccess(stored.role, pathname)) {
      router.replace(homeFor(stored.role));
      return;
    }
    setReady(true);
  }, [pathname, router]);

  function logout() {
    clearAuth();
    router.replace("/login");
  }

  if (!ready || !user) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">Memuat...</div>;
  }

  return (
    <ToastProvider>
      <div className="flex min-h-screen">
        <aside className="flex w-60 shrink-0 flex-col bg-slate-950 text-slate-200">
          <div className="border-b border-slate-800 px-5 py-5">
            <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-7 w-auto" />
            <p className="mt-2 font-mono-num text-[10px] font-bold tracking-wider text-rose-400">SCM CONTROL TOWER</p>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navFor(user.role).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive(item.href, pathname) ? "bg-[#E11D2E] text-white" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="border-t border-slate-800 px-5 py-4 text-xs">
            <p className="font-semibold text-white">{user.name}</p>
            <p className="font-mono-num text-slate-400">{user.role}</p>
            <button type="button" onClick={logout} className="mt-3 cursor-pointer text-rose-300 hover:text-rose-200">
              Keluar
            </button>
          </div>
        </aside>
        <main className="min-w-0 flex-1 p-8">{children}</main>
      </div>
    </ToastProvider>
  );
}

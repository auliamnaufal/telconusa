"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { HR_ADMIN_ROLES, consumeSsoHash } from "@/lib/auth";

export default function HRMRootRedirector() {
  const router = useRouter();

  useEffect(() => {
    consumeSsoHash().then(({ token, user }) => {
      if (!token || !user) {
        router.replace("/login");
      } else if (HR_ADMIN_ROLES.includes(user.role)) {
        router.replace("/hr");
      } else {
        router.replace("/karyawan");
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen bg-rose-50/40 flex items-center justify-center p-6">
      <div className="text-center space-y-3">
        <img src="/brand/logos/telconusa-orbit-icon.svg" alt="TelcoNusa" className="h-12 w-12 mx-auto animate-pulse" />
        <div className="text-xs font-semibold text-slate-500">Memeriksa sesi akun karyawan TelcoNusa...</div>
      </div>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { CRM_STAFF_ROLES, getAuth } from "@/lib/auth";

export default function CRMInternalRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    const { token, user } = getAuth();
    if (!token || !user || !CRM_STAFF_ROLES.includes(user.role)) {
      router.replace("/login");
      return;
    }
    if (user.role === "TECHNICIAN") {
      router.replace("/teknisi");
    } else {
      router.replace("/manager");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-300 flex flex-col items-center justify-center p-6">
      <img src="/brand/logos/telconusa-orbit-dark.svg" alt="TelcoNusa" className="h-12 w-auto mb-4" />
      <p className="text-xs font-mono-num">Mengarahkan ke CRM Internal Portal...</p>
    </div>
  );
}

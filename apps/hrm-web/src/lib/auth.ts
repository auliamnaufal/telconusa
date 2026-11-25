export const HRM_API = process.env.NEXT_PUBLIC_HRM_API_URL || "http://localhost:8002";

export interface AuthUser {
  code: string;
  name: string;
  email?: string;
  role: string;
  department?: string;
  city_code?: string;
}

const TOKEN_KEY = "tn_hrm_token";
const USER_KEY = "tn_hrm_user";

export const HR_ADMIN_ROLES = ["DIRECTOR", "HR_MANAGER", "HR_STAFF", "PAYROLL_STAFF"];

export function saveAuth(token: string, user: AuthUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getAuth(): { token: string | null; user: AuthUser | null } {
  if (typeof window === "undefined") return { token: null, user: null };
  const token = localStorage.getItem(TOKEN_KEY);
  const rawUser = localStorage.getItem(USER_KEY);
  try {
    return { token, user: rawUser ? (JSON.parse(rawUser) as AuthUser) : null };
  } catch {
    return { token: null, user: null };
  }
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function consumeSsoHash(): Promise<{ token: string | null; user: AuthUser | null }> {
  if (typeof window === "undefined") return { token: null, user: null };
  const hash = window.location.hash || "";
  if (hash.startsWith("#sso=")) {
    const token = decodeURIComponent(hash.slice(5));
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
    try {
      const res = await fetch(`${HRM_API}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        saveAuth(token, data.user);
        return { token, user: data.user };
      }
    } catch {
      // ignore failed SSO verification
    }
  }
  return getAuth();
}

export function getDivisionPortalLink(role?: string): { label: string; href: string } | null {
  if (!role) return null;
  if (["FINANCE_MANAGER", "ACCOUNTANT", "AR_STAFF", "AP_STAFF"].includes(role)) {
    return { label: "Buka Finance Suite (:3004)", href: "http://localhost:3004" };
  }
  if (["SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"].includes(role)) {
    return { label: "Buka SCM Control Tower (:3003)", href: "http://localhost:3003" };
  }
  if (role === "TECHNICIAN") {
    return { label: "Buka Field Dispatch (:3001/teknisi)", href: "http://localhost:3001/teknisi" };
  }
  if (["CRM_MANAGER", "CS_AGENT", "MARKETING", "SALES_EXEC", "SALES_MANAGER"].includes(role)) {
    return { label: "Buka CRM Operations (:3001/manager)", href: "http://localhost:3001/manager" };
  }
  if (HR_ADMIN_ROLES.includes(role)) {
    return { label: "Workspace Internal HR", href: "/hr" };
  }
  return null;
}

export function formatIDR(v: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(v);
}

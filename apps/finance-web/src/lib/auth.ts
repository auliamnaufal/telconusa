export const FINANCE_API = process.env.NEXT_PUBLIC_FINANCE_API_URL || "http://localhost:8004";
export const HRM_API = process.env.NEXT_PUBLIC_HRM_API_URL || "http://localhost:8002";
export const HRM_WEB = process.env.NEXT_PUBLIC_HRM_WEB_URL || "http://localhost:3002";

export interface AuthUser {
  code: string;
  name: string;
  email?: string;
  role: string;
  department?: string;
  city_code?: string;
}

const TOKEN_KEY = "tn_finance_token";
const USER_KEY = "tn_finance_user";

export const FINANCE_ROLES = ["DIRECTOR", "FINANCE_MANAGER", "ACCOUNTANT", "AR_STAFF", "AP_STAFF"];

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

export function buildEmployeeSsoUrl(token: string | null): string {
  if (!token) return `${HRM_WEB}/login`;
  return `${HRM_WEB}/karyawan#sso=${encodeURIComponent(token)}`;
}

export function formatIDR(v: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(v);
}

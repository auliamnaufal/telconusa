export const CRM_API = process.env.NEXT_PUBLIC_CRM_API_URL || "http://localhost:8001";
export const HRM_API = process.env.NEXT_PUBLIC_HRM_API_URL || "http://localhost:8002";

export interface CustomerUser {
  code: string;
  name: string;
  email?: string;
  whatsapp_number?: string;
  role: string;
}

const TOKEN_KEY = "tn_customer_token";
const USER_KEY = "tn_customer_user";

export function saveCustomerAuth(token: string, user: CustomerUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCustomerAuth(): { token: string | null; user: CustomerUser | null } {
  if (typeof window === "undefined") return { token: null, user: null };
  const token = localStorage.getItem(TOKEN_KEY);
  const rawUser = localStorage.getItem(USER_KEY);
  try {
    return { token, user: rawUser ? (JSON.parse(rawUser) as CustomerUser) : null };
  } catch {
    return { token: null, user: null };
  }
}

export function clearCustomerAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getSafeNextPath(nextVal: string | null, fallback = "/portal"): string {
  if (!nextVal || !nextVal.startsWith("/") || nextVal.startsWith("//")) return fallback;
  return nextVal;
}

export function formatIDR(v: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(v);
}

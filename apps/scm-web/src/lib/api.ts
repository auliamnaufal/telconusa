import { SCM_API, clearAuth, getAuth } from "@/lib/auth";

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;
  correlationId: string | null;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}, correlationId: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.correlationId = correlationId;
  }
}

function randomId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

// Satu `X-Correlation-Id` baru per aksi pengguna.
export function newCorrelationId(): string {
  return `UI-${randomId().slice(0, 12).toUpperCase()}`;
}

// Kunci untuk `POST` transaksi; buat sekali per aksi dan pakai ulang saat mencoba lagi.
export function newIdempotencyKey(): string {
  return randomId();
}

// Mengurai galat baku `{ error: { code, message, details, correlation_id } }`; cadangan untuk bentuk lain.
export function parseError(status: number, body: unknown): ApiError {
  const error = (body as { error?: Record<string, unknown> } | null)?.error;
  if (error && typeof error.message === "string") {
    return new ApiError(
      status,
      typeof error.code === "string" ? error.code : `HTTP_${status}`,
      error.message,
      (error.details as Record<string, unknown>) ?? {},
      typeof error.correlation_id === "string" ? error.correlation_id : null,
    );
  }
  const detail = (body as { detail?: unknown } | null)?.detail;
  return new ApiError(status, `HTTP_${status}`, typeof detail === "string" ? detail : `Permintaan gagal (HTTP ${status})`);
}

export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  idempotencyKey?: string;
  correlationId?: string;
  signal?: AbortSignal;
}

export async function api<T = unknown>(path: string, options: ApiOptions = {}): Promise<T> {
  const { token } = getAuth();
  const headers: Record<string, string> = {
    "X-Correlation-Id": options.correlationId ?? newCorrelationId(),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;

  const response = await fetch(`${SCM_API}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
    signal: options.signal,
  });

  if (response.status === 204) return undefined as T;
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (response.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") window.location.assign("/login");
  }
  if (!response.ok) throw parseError(response.status, body);
  return body as T;
}

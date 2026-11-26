import { api, newIdempotencyKey } from "@/lib/api";
import type { ListFilters, StockRequestDetail, StockRequestSummary } from "./types";

const BASE = "/api/v1/stock-requests";

export function listStockRequests(filters: ListFilters, signal?: AbortSignal): Promise<StockRequestSummary[]> {
  const query = new URLSearchParams({ page: String(filters.page), limit: String(filters.limit) });
  if (filters.status) query.set("status", filters.status);
  if (filters.city_code) query.set("city_code", filters.city_code);
  if (filters.ticket_code.trim()) query.set("ticket_code", filters.ticket_code.trim());
  return api<StockRequestSummary[]>(`${BASE}?${query.toString()}`, { signal });
}

export function getStockRequest(no: string, signal?: AbortSignal): Promise<StockRequestDetail> {
  return api<StockRequestDetail>(`${BASE}/${encodeURIComponent(no)}`, { signal });
}

export { newIdempotencyKey };

export function issueStockRequest(no: string, lines: { item_sku: string; qty: number }[], key: string) {
  return api<{ stock_request_no: string; status: string; unit_status: string }>(`${BASE}/${encodeURIComponent(no)}/issue`, {
    method: "POST",
    body: { lines },
    idempotencyKey: key,
  });
}

export function issueExtra(no: string, lines: { item_sku: string; qty: number }[], key: string) {
  return api<{ stock_request_no: string; status: string; lines_added: number }>(`${BASE}/${encodeURIComponent(no)}/issue-extra`, {
    method: "POST",
    body: { lines },
    idempotencyKey: key,
  });
}

export function flagDamaged(
  no: string,
  body: { item_sku: string; qty: number; serial_number?: string; notes?: string },
  key: string,
) {
  return api<{ stock_request_no: string; item_sku: string; qty_damaged: number }>(`${BASE}/${encodeURIComponent(no)}/flag-damaged`, {
    method: "POST",
    body,
    idempotencyKey: key,
  });
}

export function cancelStockRequest(no: string, reason: string, key: string) {
  return api<{ stock_request_no: string; status: string }>(`${BASE}/${encodeURIComponent(no)}/cancel`, {
    method: "POST",
    body: { reason },
    idempotencyKey: key,
  });
}

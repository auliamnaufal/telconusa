import { api } from "@/lib/api";
import type {
  CreatedPurchaseOrder,
  PurchaseOrderDetail,
  PurchaseOrderSummary,
  PurchaseRequestDetail,
  PurchaseRequestSummary,
} from "./types";

const PR = "/api/v1/purchase-requests";
const PO = "/api/v1/purchase-orders";

function listQuery(status: string, page: number, limit: number): string {
  const query = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (status) query.set("status", status);
  return query.toString();
}

export function listPurchaseRequests(status: string, page: number, limit: number, signal?: AbortSignal) {
  return api<PurchaseRequestSummary[]>(`${PR}?${listQuery(status, page, limit)}`, { signal });
}

export function getPurchaseRequest(no: string, signal?: AbortSignal) {
  return api<PurchaseRequestDetail>(`${PR}/${encodeURIComponent(no)}`, { signal });
}

export function listPurchaseOrders(status: string, page: number, limit: number, signal?: AbortSignal) {
  return api<PurchaseOrderSummary[]>(`${PO}?${listQuery(status, page, limit)}`, { signal });
}

export function getPurchaseOrder(no: string, signal?: AbortSignal) {
  return api<PurchaseOrderDetail>(`${PO}/${encodeURIComponent(no)}`, { signal });
}

export function createPurchaseOrder(body: { vendor_code: string; item_sku: string; qty: number }, key: string) {
  return api<CreatedPurchaseOrder>(PO, { method: "POST", body, idempotencyKey: key });
}

export function createPoFromRequest(
  no: string,
  body: { vendor_code: string; unit_prices: { item_sku: string; unit_price: number }[] },
  key: string,
) {
  return api<CreatedPurchaseOrder>(`${PR}/${encodeURIComponent(no)}/create-po`, { method: "POST", body, idempotencyKey: key });
}

export function decidePurchaseOrder(no: string, action: "approve" | "reject", comment: string | null, key: string) {
  return api<PurchaseOrderDetail>(`${PO}/${encodeURIComponent(no)}/${action}`, {
    method: "POST",
    body: { comment },
    idempotencyKey: key,
  });
}

export function addQuote(no: string, body: { vendor_code: string; unit_price: number; notes: string | null }, key: string) {
  return api<PurchaseOrderDetail>(`${PO}/${encodeURIComponent(no)}/quotes`, { method: "POST", body, idempotencyKey: key });
}

export function submitPurchaseOrder(no: string, key: string) {
  return api<PurchaseOrderDetail>(`${PO}/${encodeURIComponent(no)}/submit`, { method: "POST", idempotencyKey: key });
}

export function receiveGoods(
  no: string,
  body: { warehouse_code: string; lines: { item_sku: string; qty: number }[] },
  key: string,
) {
  return api<{ gr_no: string; po_status: string; serial_numbers: string[] }>(`${PO}/${encodeURIComponent(no)}/receipts`, {
    method: "POST",
    body,
    idempotencyKey: key,
  });
}

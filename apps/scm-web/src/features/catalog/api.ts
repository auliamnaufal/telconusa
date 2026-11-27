import { api, newIdempotencyKey } from "@/lib/api";

// Bentuk respons scm-api (contracts/openapi/scm.yaml dan tracks/scm/contract-extension.md).

export interface DashboardSummary {
  kpis: {
    total_skus: number;
    inventory_valuation_idr: number;
    open_stock_requests: number;
    return_pending: number;
    active_reservations: number;
    open_purchase_orders: number;
    ont_installed: number;
  };
  stock_requests: { stock_request_no: string; ticket_code: string; status: string }[];
}

export interface StockBalance {
  warehouse_code: string;
  item_sku: string;
  name: string;
  unit: string;
  qty_physical: number;
  qty_reserved: number;
  qty_damaged: number;
  qty_available: number;
  reorder_point: number;
  below_rop: boolean;
}

export interface Item {
  sku: string;
  name: string;
  unit: string;
  unit_cost: number;
  reorder_point: number;
  safety_stock: number;
  is_serialized: boolean;
  specification: string | null;
}

export interface Warehouse {
  code: string;
  name: string;
  city_code: string;
}

export interface Vendor {
  code: string;
  name: string;
  category: string;
  rating_score: number | null;
}

export interface PackageKit {
  service_sku: string;
  items: { item_sku: string; name: string; qty: number; unit: string }[];
}

export function getDashboardSummary(signal?: AbortSignal) {
  return api<DashboardSummary>("/api/v1/dashboard/summary", { signal });
}

export interface BalanceFilters {
  warehouse_code: string;
  item_sku: string;
  page: number;
  limit: number;
}

export function listBalances(filters: BalanceFilters, signal?: AbortSignal) {
  const query = new URLSearchParams({ page: String(filters.page), limit: String(filters.limit) });
  if (filters.warehouse_code) query.set("warehouse_code", filters.warehouse_code);
  if (filters.item_sku) query.set("item_sku", filters.item_sku);
  return api<StockBalance[]>(`/api/v1/stock/balances?${query.toString()}`, { signal });
}

export function listItems(signal?: AbortSignal) {
  return api<Item[]>("/api/v1/items?limit=100", { signal });
}

export function listWarehouses(signal?: AbortSignal) {
  return api<Warehouse[]>("/api/v1/warehouses?limit=100", { signal });
}

export function listVendors(signal?: AbortSignal) {
  return api<Vendor[]>("/api/v1/vendors?limit=100", { signal });
}

export function listPackageKits(signal?: AbortSignal) {
  return api<PackageKit[]>("/api/v1/package-kits?limit=100", { signal });
}

export type ItemInput = Omit<Item, "specification"> & { specification: string | null };

export function createItem(body: ItemInput, key: string) {
  return api<Item>("/api/v1/items", { method: "POST", body, idempotencyKey: key });
}

export function updateItem(sku: string, body: Partial<Omit<Item, "sku">>) {
  return api<Item>(`/api/v1/items/${encodeURIComponent(sku)}`, { method: "PATCH", body });
}

export function createVendor(body: { name: string; category: string; rating_score: number }, key: string) {
  return api<Vendor>("/api/v1/vendors", { method: "POST", body, idempotencyKey: key });
}

export function updateVendor(code: string, body: Partial<Omit<Vendor, "code">>) {
  return api<Vendor>(`/api/v1/vendors/${encodeURIComponent(code)}`, { method: "PATCH", body });
}

export function replacePackageKit(serviceSku: string, lines: { item_sku: string; qty: number }[]) {
  return api<PackageKit>(`/api/v1/package-kits/${encodeURIComponent(serviceSku)}`, { method: "PUT", body: { lines } });
}

export { newIdempotencyKey };

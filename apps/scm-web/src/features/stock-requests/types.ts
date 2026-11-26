export type StockRequestStatus = "REQUESTED" | "PENDING_STOCK" | "READY_TO_ISSUE" | "ISSUED" | "RETURNED" | "CANCELLED";

export interface StockRequestSummary {
  stock_request_no: string;
  ticket_code: string;
  status: StockRequestStatus;
  technician_employee_id: string | null;
  city_code: string;
  return_pending: boolean;
}

export interface StockRequestLine {
  item_sku: string;
  qty_required: number;
  qty_issued: number;
  qty_used: number;
  qty_returned: number;
  qty_damaged: number;
  unit: string;
  is_extra: boolean;
}

export interface StockRequestDetail extends StockRequestSummary {
  warehouse_code: string;
  reserved_until: string | null;
  purchase_request_no: string | null;
  discrepancy: boolean;
  cancel_reason: string | null;
  lines: StockRequestLine[];
}

export interface ListFilters {
  status: string;
  city_code: string;
  ticket_code: string;
  page: number;
  limit: number;
}

// Peran yang boleh mengubah permintaan barang (spec bagian 1.2).
export const WAREHOUSE_ROLES = ["SCM_MANAGER", "WAREHOUSE_STAFF"];
export const STATUSES: StockRequestStatus[] = ["REQUESTED", "PENDING_STOCK", "READY_TO_ISSUE", "ISSUED", "RETURNED", "CANCELLED"];
export const CITIES = ["JKT", "BDG", "SBY"];

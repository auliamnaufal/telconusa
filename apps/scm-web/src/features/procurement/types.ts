export type PurchaseRequestStatus = "PENDING_BUDGET" | "BUDGET_OK" | "BUDGET_REJECTED" | "PO_CREATED" | "CANCELLED";
export type PurchaseOrderStatus =
  | "DRAFT"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CLOSED"
  | "REJECTED"
  | "CANCELLED";

export type PurchaseRequestSummary = {
  purchase_request_no: string;
  source: "STOCK_REQUEST" | "LOW_STOCK" | "MANUAL";
  stock_request_no: string | null;
  warehouse_code: string;
  estimated_total: number;
  status: PurchaseRequestStatus;
  budget_checked_at: string | null;
  budget_remaining: number | null;
  created_at: string | null;
};

export type PurchaseRequestDetail = PurchaseRequestSummary & {
  po_no: string | null;
  lines: { item_sku: string; qty: number; estimated_unit_cost: number }[];
};

export type PurchaseOrderSummary = {
  po_no: string;
  purchase_request_no: string | null;
  vendor_code: string;
  total_amount: number;
  status: PurchaseOrderStatus;
  required_roles: string[];
  created_by: string;
  created_at: string | null;
};

export type PurchaseOrderLine = { item_sku: string; qty: number; unit_price: number; qty_received: number };

export type PurchaseOrderDetail = PurchaseOrderSummary & {
  vendor_name: string | null;
  warehouse_code: string | null;
  lines: PurchaseOrderLine[];
  quotes: { vendor_code: string; unit_price: number; notes: string | null; created_by: string; created_at: string | null }[];
  approvals: { role: string; approver_id: string; decision: "APPROVED" | "REJECTED"; comment: string | null; at: string | null }[];
  receipts: {
    gr_no: string;
    warehouse_code: string;
    received_by: string;
    received_at: string | null;
    lines: { item_sku: string; qty: number; serial_numbers: string[] }[];
  }[];
};

export type CreatedPurchaseOrder = {
  po_no: string;
  total_amount: number;
  status: PurchaseOrderStatus;
  budget_remaining_after_check: number;
};

// Peran per aksi (spec bagian 1.2 dan 8); server tetap penentu.
export const PROCUREMENT_ROLES = ["SCM_MANAGER", "PROCUREMENT_STAFF"];
export const RECEIVING_ROLES = ["SCM_MANAGER", "WAREHOUSE_STAFF"];
export const PR_READ_ROLES = ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"];

export const PR_STATUSES: PurchaseRequestStatus[] = ["PENDING_BUDGET", "BUDGET_OK", "BUDGET_REJECTED", "PO_CREATED", "CANCELLED"];
// Sama dengan aturan server (spec F9).
export const MIN_QUOTES = 3;

export const PO_STATUSES: PurchaseOrderStatus[] = [
  "DRAFT",
  "PENDING_APPROVAL",
  "APPROVED",
  "PARTIALLY_RECEIVED",
  "RECEIVED",
  "REJECTED",
  "CANCELLED",
];

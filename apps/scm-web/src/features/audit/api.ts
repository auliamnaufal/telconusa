import { api } from "@/lib/api";

export interface AuditLogEntry {
  id: string;
  at: string | null;
  actor: string;
  role: string | null;
  action: string;
  entity: string;
  entity_id: string;
  detail: unknown;
  correlation_id: string | null;
}

export interface AuditFilters {
  entity: string;
  entity_id: string;
  actor: string;
  page: number;
  limit: number;
}

// Entitas yang dicatat `core.audit.record` saat ini.
export const ENTITIES = ["StockRequest", "Item", "Vendor", "PackageKit"];

export function listAuditLogs(filters: AuditFilters, signal?: AbortSignal): Promise<AuditLogEntry[]> {
  const query = new URLSearchParams({ page: String(filters.page), limit: String(filters.limit) });
  if (filters.entity) query.set("entity", filters.entity);
  if (filters.entity_id.trim()) query.set("entity_id", filters.entity_id.trim());
  if (filters.actor.trim()) query.set("actor", filters.actor.trim());
  return api<AuditLogEntry[]>(`/api/v1/audit-logs?${query.toString()}`, { signal });
}

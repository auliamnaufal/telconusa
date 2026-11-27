"""Permintaan pembelian (PR) dan implementasi `ProcurementPort`.

Port dipanggil Slice A di dalam transaksi event atau pengeluaran barang, jadi ia hanya membuat PR
`PENDING_BUDGET` tanpa memanggil Finance. Cek anggaran dijalankan pekerjaan berkala, sehingga
transaksi stok tidak menunggu jaringan.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.core import audit, clock, machines
from app.core.codes import new_purchase_request_no
from app.core.errors import ScmError
from app.core.models import AuditLog, Item
from app.core.ports import Shortage
from app.procurement import finance_client
from app.procurement.models import PurchaseOrder, PurchaseRequest, PurchaseRequestLine

SYSTEM_ACTOR = "system"
ENTITY = "PurchaseRequest"
OPEN_STATUSES = ("PENDING_BUDGET", "BUDGET_OK")


def get_by_no(db: Session, pr_no: str, for_update: bool = False) -> PurchaseRequest:
    query = db.query(PurchaseRequest).filter(PurchaseRequest.pr_no == pr_no)
    if for_update:
        query = query.with_for_update().populate_existing()
    request = query.first()
    if request is None:
        raise ScmError(
            "PURCHASE_REQUEST_NOT_FOUND",
            f"Permintaan pembelian {pr_no} tidak ditemukan",
            404,
            {"purchase_request_no": pr_no},
        )
    return request


def transition(request: PurchaseRequest, new_status: str) -> None:
    machines.PURCHASE_REQUEST.assert_transition(request.status, new_status)
    request.status = new_status
    request.version = (request.version or 1) + 1


def create(
    db: Session,
    *,
    source: str,
    warehouse_code: str,
    lines: list[tuple[str, int, int]],
    actor: Any,
    correlation_id: str,
    stock_request_no: str | None = None,
) -> PurchaseRequest:
    """Buat PR `PENDING_BUDGET`; `lines` berisi `(item_sku, qty, perkiraan harga satuan)`."""
    request = PurchaseRequest(
        pr_no=new_purchase_request_no(db),
        source=source,
        stock_request_no=stock_request_no,
        warehouse_code=warehouse_code,
        estimated_total=sum(qty * cost for _, qty, cost in lines),
        status="PENDING_BUDGET",
        created_by=getattr(actor, "sub", actor),
    )
    request.lines = [PurchaseRequestLine(item_sku=sku, qty=qty, estimated_unit_cost=cost) for sku, qty, cost in lines]
    db.add(request)
    db.flush()
    audit.record(
        db, actor, "purchase_request.create", ENTITY, request.pr_no,
        {"source": source, "estimated_total": request.estimated_total, "stock_request_no": stock_request_no},
        correlation_id,
    )
    db.flush()
    return request


def apply_budget_result(
    db: Session,
    request: PurchaseRequest,
    result: finance_client.BudgetResult,
    actor: Any,
    correlation_id: str,
) -> None:
    transition(request, "BUDGET_OK" if result.approved else "BUDGET_REJECTED")
    request.budget_checked_at = clock.utcnow()
    request.budget_remaining = result.remaining
    audit.record(
        db, actor, "purchase_request.budget_check", ENTITY, request.pr_no,
        {"approved": result.approved, "remaining": result.remaining, "amount": request.estimated_total},
        correlation_id,
    )


def _correlation_of(db: Session, pr_no: str) -> str:
    """`X-Correlation-Id` asal PR (tiket pemicunya), dibaca dari audit pembuatan."""
    row = (
        db.query(AuditLog.correlation_id)
        .filter(AuditLog.entity == ENTITY, AuditLog.entity_id == pr_no, AuditLog.action == "purchase_request.create")
        .first()
    )
    return row[0] if row and row[0] else pr_no


def check_pending_budgets(db: Session) -> list[str]:
    """Periksa semua PR `PENDING_BUDGET`; kembalikan nomor PR yang mendapat jawaban.

    Commit per PR supaya satu kegagalan tidak membatalkan jawaban yang sudah diterima, dan baris
    PR tidak dikunci selama menunggu Finance.
    """
    pending = (
        db.query(PurchaseRequest.pr_no, PurchaseRequest.estimated_total)
        .filter(PurchaseRequest.status == "PENDING_BUDGET")
        .order_by(PurchaseRequest.created_at, PurchaseRequest.pr_no)
        .all()
    )
    answered: list[str] = []
    for pr_no, amount in pending:
        correlation_id = _correlation_of(db, pr_no)
        result = finance_client.check_budget(amount, correlation_id)
        if result is None:
            continue
        request = get_by_no(db, pr_no, for_update=True)
        if request.status == "PENDING_BUDGET":
            apply_budget_result(db, request, result, SYSTEM_ACTOR, correlation_id)
            answered.append(pr_no)
        db.commit()
    return answered


def to_summary(request: PurchaseRequest) -> dict[str, Any]:
    return {
        "purchase_request_no": request.pr_no,
        "source": request.source,
        "stock_request_no": request.stock_request_no,
        "warehouse_code": request.warehouse_code,
        "estimated_total": request.estimated_total,
        "status": request.status,
        "budget_checked_at": clock.to_wib_iso(request.budget_checked_at),
        "budget_remaining": request.budget_remaining,
        "created_at": clock.to_wib_iso(request.created_at),
    }


def to_detail(db: Session, request: PurchaseRequest) -> dict[str, Any]:
    order = db.query(PurchaseOrder.po_no).filter(PurchaseOrder.purchase_request_no == request.pr_no).first()
    return {
        **to_summary(request),
        "po_no": order[0] if order else None,
        "lines": [
            {"item_sku": line.item_sku, "qty": line.qty, "estimated_unit_cost": line.estimated_unit_cost}
            for line in sorted(request.lines, key=lambda line: line.item_sku)
        ],
    }


def list_requests(db: Session, status: str | None, page: int, limit: int) -> tuple[list[PurchaseRequest], int]:
    query = db.query(PurchaseRequest)
    if status:
        query = query.filter(PurchaseRequest.status == status)
    total = query.count()
    rows = (
        query.order_by(PurchaseRequest.created_at.desc(), PurchaseRequest.pr_no.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return rows, total


class ProcurementService:
    """Implementasi `ProcurementPort` (dipanggil Slice A)."""

    def request_purchase(
        self,
        db: Session,
        *,
        stock_request_no: str,
        warehouse_code: str,
        shortages: list[Shortage],
        correlation_id: str,
    ) -> str:
        existing = (
            db.query(PurchaseRequest)
            .filter(PurchaseRequest.source == "STOCK_REQUEST", PurchaseRequest.stock_request_no == stock_request_no)
            .first()
        )
        if existing is not None:
            return existing.pr_no

        quantities: dict[str, int] = {}
        for shortage in shortages:
            quantities[shortage.item_sku] = quantities.get(shortage.item_sku, 0) + shortage.qty
        if not quantities or any(qty <= 0 for qty in quantities.values()):
            raise ScmError("INVALID_QUANTITY", "PR memerlukan kekurangan dengan jumlah lebih dari 0", 422)

        request = create(
            db,
            source="STOCK_REQUEST",
            warehouse_code=warehouse_code,
            lines=[(sku, qty, _unit_cost(db, sku)) for sku, qty in quantities.items()],
            actor=SYSTEM_ACTOR,
            correlation_id=correlation_id,
            stock_request_no=stock_request_no,
        )
        return request.pr_no

    def request_low_stock_purchase(
        self,
        db: Session,
        *,
        item_sku: str,
        warehouse_code: str,
        qty: int,
        correlation_id: str,
    ) -> str | None:
        existing = (
            db.query(PurchaseRequest)
            .join(PurchaseRequestLine, PurchaseRequestLine.purchase_request_id == PurchaseRequest.id)
            .filter(
                PurchaseRequest.source == "LOW_STOCK",
                PurchaseRequest.status.in_(OPEN_STATUSES),
                PurchaseRequest.warehouse_code == warehouse_code,
                PurchaseRequestLine.item_sku == item_sku,
            )
            .first()
        )
        if existing is not None:
            return existing.pr_no
        if qty <= 0:
            raise ScmError("INVALID_QUANTITY", "Jumlah PR harus lebih dari 0", 422, {"qty": qty})

        request = create(
            db,
            source="LOW_STOCK",
            warehouse_code=warehouse_code,
            lines=[(item_sku, qty, _unit_cost(db, item_sku))],
            actor=SYSTEM_ACTOR,
            correlation_id=correlation_id,
        )
        return request.pr_no


def _unit_cost(db: Session, sku: str) -> int:
    item = db.get(Item, sku)
    if item is None:
        raise ScmError("UNKNOWN_ITEM", f"Barang {sku} tidak dikenal", 422, {"item_sku": sku})
    return item.unit_cost

"""Purchase order: pembuatan, persetujuan berjenjang, dan pembacaan (spec F8.2 dan F8.3).

Semua fungsi berjalan di transaksi pemanggil dan tidak melakukan commit.
"""
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core import audit, clock, machines
from app.core.auth import Actor
from app.core.codes import new_purchase_order_no
from app.core.errors import ScmError
from app.core.models import Item, Vendor
from app.procurement import finance_client, purchase_requests
from app.procurement.models import (
    GoodsReceipt,
    PoApproval,
    PoQuote,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
)

ENTITY = "PurchaseOrder"
# `POST /purchase-orders` (kontrak) tidak membawa gudang: PR manual dicatat pada gudang pusat.
# Gudang penerima barang tetap dipilih saat penerimaan.
CENTRAL_WAREHOUSE = "WH-BKS"

MANAGER_LIMIT = 10_000_000
FINANCE_LIMIT = 100_000_000
# PO di atas nilai ini lahir `DRAFT` dan butuh penawaran sebelum diajukan (spec F9).
QUOTE_THRESHOLD = 50_000_000
MIN_QUOTES = 3


def required_roles_for(total: int) -> list[str]:
    roles = ["SCM_MANAGER"]
    if total > MANAGER_LIMIT:
        roles.append("FINANCE_MANAGER")
    if total > FINANCE_LIMIT:
        roles.append("DIRECTOR")
    return roles


def get_by_no(db: Session, po_no: str, for_update: bool = False) -> PurchaseOrder:
    query = db.query(PurchaseOrder).filter(PurchaseOrder.po_no == po_no)
    if for_update:
        query = query.with_for_update().populate_existing()
    order = query.first()
    if order is None:
        raise ScmError("PURCHASE_ORDER_NOT_FOUND", f"PO {po_no} tidak ditemukan", 404, {"po_no": po_no})
    return order


def transition(order: PurchaseOrder, new_status: str) -> None:
    machines.PURCHASE_ORDER.assert_transition(order.status, new_status)
    order.status = new_status
    order.version = (order.version or 1) + 1


def _vendor(db: Session, vendor_code: str) -> Vendor:
    vendor = db.get(Vendor, vendor_code)
    if vendor is None:
        raise ScmError("VENDOR_NOT_FOUND", f"Vendor {vendor_code} tidak dikenal", 404, {"vendor_code": vendor_code})
    return vendor


def _require_budget(amount: int, correlation_id: str) -> finance_client.BudgetResult:
    """Cek anggaran yang menahan: tidak terjangkau -> 503, tidak cukup -> 409."""
    result = finance_client.check_budget(amount, correlation_id)
    if result is None:
        raise ScmError(
            "BUDGET_CHECK_UNAVAILABLE",
            "Cek anggaran Finance tidak tersedia; PO tidak dibuat. Coba lagi nanti.",
            503,
            {"amount": amount},
            correlation_id,
        )
    if not result.approved:
        raise ScmError(
            "BUDGET_INSUFFICIENT",
            "Sisa anggaran tidak cukup untuk PO ini",
            409,
            {"amount": amount, "remaining": result.remaining},
            correlation_id,
        )
    return result


def _build(
    db: Session,
    request: PurchaseRequest,
    vendor_code: str,
    lines: list[tuple[str, int, int]],
    actor: Actor,
    correlation_id: str,
) -> PurchaseOrder:
    total = sum(qty * price for _, qty, price in lines)
    purchase_requests.transition(request, "PO_CREATED")
    order = PurchaseOrder(
        po_no=new_purchase_order_no(db),
        purchase_request_no=request.pr_no,
        vendor_code=vendor_code,
        total_amount=total,
        status="DRAFT" if total > QUOTE_THRESHOLD else "PENDING_APPROVAL",
        required_roles=json.dumps(required_roles_for(total)),
        created_by=actor.sub,
    )
    order.lines = [PurchaseOrderLine(item_sku=sku, qty=qty, unit_price=price) for sku, qty, price in lines]
    db.add(order)
    db.flush()
    audit.record(
        db, actor, "purchase_order.create", ENTITY, order.po_no,
        {"purchase_request_no": request.pr_no, "vendor_code": vendor_code, "total_amount": total},
        correlation_id,
    )
    return order


def _created(order: PurchaseOrder, remaining: int) -> dict[str, Any]:
    return {
        "po_no": order.po_no,
        "total_amount": order.total_amount,
        "status": order.status,
        "budget_remaining_after_check": remaining,
    }


def create_direct(
    db: Session, vendor_code: str, item_sku: str, qty: int, actor: Actor, correlation_id: str
) -> dict[str, Any]:
    """`POST /purchase-orders`: cek anggaran dulu, lalu PR dan PO dibuat dalam satu transaksi."""
    _vendor(db, vendor_code)
    item = db.get(Item, item_sku)
    if item is None:
        raise ScmError("ITEM_NOT_FOUND", f"Barang {item_sku} tidak dikenal", 404, {"item_sku": item_sku})

    budget = _require_budget(qty * item.unit_cost, correlation_id)

    request = purchase_requests.create(
        db,
        source="MANUAL",
        warehouse_code=CENTRAL_WAREHOUSE,
        lines=[(item_sku, qty, item.unit_cost)],
        actor=actor,
        correlation_id=correlation_id,
    )
    purchase_requests.apply_budget_result(db, request, budget, actor, correlation_id)
    order = _build(db, request, vendor_code, [(item_sku, qty, item.unit_cost)], actor, correlation_id)
    return _created(order, budget.remaining)


def create_from_request(
    db: Session,
    pr_no: str,
    vendor_code: str,
    unit_prices: list[tuple[str, int]],
    actor: Actor,
    correlation_id: str,
) -> dict[str, Any]:
    """`POST /purchase-requests/{no}/create-po` untuk PR `BUDGET_OK`."""
    request = purchase_requests.get_by_no(db, pr_no, for_update=True)
    machines.PURCHASE_REQUEST.assert_transition(request.status, "PO_CREATED")
    _vendor(db, vendor_code)

    prices = dict(unit_prices)
    expected = {line.item_sku for line in request.lines}
    if len(prices) != len(unit_prices) or set(prices) != expected:
        raise ScmError(
            "PRICE_LINES_MISMATCH",
            "unit_prices harus memuat tepat satu harga untuk setiap barang di PR",
            422,
            {"expected": sorted(expected), "provided": [sku for sku, _ in unit_prices]},
        )
    lines = [(line.item_sku, line.qty, prices[line.item_sku]) for line in request.lines]
    total = sum(qty * price for _, qty, price in lines)

    remaining = request.budget_remaining
    # Anggaran yang disetujui hanya sebesar perkiraan PR; nilai yang lebih besar diperiksa ulang.
    if total > request.estimated_total:
        remaining = _require_budget(total, correlation_id).remaining

    order = _build(db, request, vendor_code, lines, actor, correlation_id)
    return _created(order, remaining)


def decide(db: Session, po_no: str, decision: str, comment: str | None, actor: Actor) -> dict[str, Any]:
    """Catat satu keputusan (`APPROVED` atau `REJECTED`) menurut aturan F8.3."""
    order = get_by_no(db, po_no, for_update=True)
    machines.PURCHASE_ORDER.assert_transition(order.status, decision)
    if order.created_by == actor.sub:
        raise ScmError(
            "APPROVAL_SELF_FORBIDDEN", "Pembuat PO tidak boleh memutuskan PO-nya sendiri", 403, correlation_id=po_no
        )
    required = json.loads(order.required_roles)
    if actor.role not in required:
        raise ScmError(
            "APPROVAL_ROLE_NOT_REQUIRED",
            f"Role {actor.role} tidak ada dalam rantai persetujuan PO ini",
            403,
            {"required_roles": required},
            po_no,
        )
    # Baca dengan kunci: keputusan yang baru di-commit penyetuju lain harus ikut terbaca.
    decided = db.query(PoApproval).filter(PoApproval.purchase_order_id == order.id).with_for_update().all()
    if any(approval.role == actor.role for approval in decided):
        raise ScmError("DUPLICATE_APPROVAL", f"Role {actor.role} sudah memutuskan PO ini", 409, correlation_id=po_no)

    order.approvals.append(
        PoApproval(role=actor.role, approver_id=actor.sub, decision=decision, comment=comment, at=clock.utcnow())
    )
    approved_roles = {approval.role for approval in decided if approval.decision == "APPROVED"}
    if decision == "REJECTED":
        transition(order, "REJECTED")
    elif set(required) <= approved_roles | {actor.role}:
        transition(order, "APPROVED")
    else:
        order.version = (order.version or 1) + 1
    audit.record(
        db, actor, f"purchase_order.{'approve' if decision == 'APPROVED' else 'reject'}", ENTITY, po_no,
        {"comment": comment, "status": order.status}, po_no,
    )
    db.flush()
    db.expire(order, ["approvals"])
    return to_detail(db, order)


def _quotes(db: Session, po_no: str, for_update: bool = False) -> list[PoQuote]:
    query = db.query(PoQuote).filter(PoQuote.po_no == po_no)
    if for_update:  # baca dengan kunci: penawaran yang baru di-commit pengguna lain harus ikut terbaca
        query = query.with_for_update()
    return query.order_by(PoQuote.unit_price, PoQuote.vendor_code).all()


def add_quote(
    db: Session, po_no: str, vendor_code: str, unit_price: int, notes: str | None, actor: Actor
) -> dict[str, Any]:
    """Catat satu penawaran pada PO `DRAFT`; satu vendor hanya sekali."""
    order = get_by_no(db, po_no, for_update=True)
    if order.status != "DRAFT":
        raise ScmError(
            "INVALID_TRANSITION",
            f"PURCHASE_ORDER: penawaran hanya untuk PO DRAFT, status sekarang {order.status}",
            409,
            {"machine": "PURCHASE_ORDER", "current": order.status, "requested": "ADD_QUOTE", "allowed": ["DRAFT"]},
            po_no,
        )
    _vendor(db, vendor_code)
    if any(quote.vendor_code == vendor_code for quote in _quotes(db, po_no, for_update=True)):
        raise ScmError(
            "DUPLICATE_QUOTE", f"Vendor {vendor_code} sudah memberi penawaran untuk PO ini", 409,
            {"vendor_code": vendor_code}, po_no,
        )
    db.add(PoQuote(po_no=po_no, vendor_code=vendor_code, unit_price=unit_price, notes=notes, created_by=actor.sub))
    order.version = (order.version or 1) + 1
    audit.record(
        db, actor, "purchase_order.add_quote", ENTITY, po_no,
        {"vendor_code": vendor_code, "unit_price": unit_price}, po_no,
    )
    db.flush()
    return to_detail(db, order)


def submit(db: Session, po_no: str, actor: Actor) -> dict[str, Any]:
    """`DRAFT` -> `PENDING_APPROVAL` setelah penawaran cukup."""
    order = get_by_no(db, po_no, for_update=True)
    machines.PURCHASE_ORDER.assert_transition(order.status, "PENDING_APPROVAL")
    count = len(_quotes(db, po_no, for_update=True))
    if count < MIN_QUOTES:
        raise ScmError(
            "QUOTES_REQUIRED",
            f"PO ini butuh {MIN_QUOTES} penawaran dari vendor berbeda, baru ada {count}",
            409,
            {"required": MIN_QUOTES, "provided": count},
            po_no,
        )
    transition(order, "PENDING_APPROVAL")
    audit.record(db, actor, "purchase_order.submit", ENTITY, po_no, {"quotes": count}, po_no)
    db.flush()
    return to_detail(db, order)


def to_summary(order: PurchaseOrder) -> dict[str, Any]:
    return {
        "po_no": order.po_no,
        "purchase_request_no": order.purchase_request_no,
        "vendor_code": order.vendor_code,
        "total_amount": order.total_amount,
        "status": order.status,
        "required_roles": json.loads(order.required_roles),
        "created_by": order.created_by,
        "created_at": clock.to_wib_iso(order.created_at),
    }


def to_detail(db: Session, order: PurchaseOrder) -> dict[str, Any]:
    vendor = db.get(Vendor, order.vendor_code)
    warehouse = (
        db.query(PurchaseRequest.warehouse_code).filter(PurchaseRequest.pr_no == order.purchase_request_no).first()
    )
    receipts = db.query(GoodsReceipt).filter(GoodsReceipt.po_no == order.po_no).order_by(GoodsReceipt.gr_no).all()
    return {
        **to_summary(order),
        "vendor_name": vendor.name if vendor else None,
        "warehouse_code": warehouse[0] if warehouse else None,
        "lines": [
            {"item_sku": line.item_sku, "qty": line.qty, "unit_price": line.unit_price, "qty_received": line.qty_received}
            for line in sorted(order.lines, key=lambda line: line.item_sku)
        ],
        "approvals": [
            {
                "role": approval.role,
                "approver_id": approval.approver_id,
                "decision": approval.decision,
                "comment": approval.comment,
                "at": clock.to_wib_iso(approval.at),
            }
            for approval in sorted(order.approvals, key=lambda approval: (approval.at, approval.role))
        ],
        "quotes": [
            {
                "vendor_code": quote.vendor_code,
                "unit_price": quote.unit_price,
                "notes": quote.notes,
                "created_by": quote.created_by,
                "created_at": clock.to_wib_iso(quote.created_at),
            }
            for quote in _quotes(db, order.po_no)
        ],
        "receipts": [
            {
                "gr_no": receipt.gr_no,
                "warehouse_code": receipt.warehouse_code,
                "received_by": receipt.received_by,
                "received_at": clock.to_wib_iso(receipt.received_at),
                "lines": [
                    {
                        "item_sku": line.item_sku,
                        "qty": line.qty,
                        "serial_numbers": json.loads(line.serial_numbers) if line.serial_numbers else [],
                    }
                    for line in receipt.lines
                ],
            }
            for receipt in receipts
        ],
    }


def list_orders(db: Session, status: str | None, page: int, limit: int) -> tuple[list[PurchaseOrder], int]:
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    total = query.count()
    rows = (
        query.order_by(PurchaseOrder.created_at.desc(), PurchaseOrder.po_no.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return rows, total

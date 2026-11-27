"""Penerimaan barang (GR, spec F8.4). Berjalan di transaksi pemanggil tanpa commit."""
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core import audit, clock, ledger
from app.core.auth import Actor
from app.core.codes import new_goods_receipt_no
from app.core.errors import ScmError
from app.core.models import Item, Warehouse
from app.core.ports import ports
from app.procurement import purchase_orders
from app.procurement.models import GoodsReceipt, GoodsReceiptLine, PurchaseOrderLine

RECEIVABLE = ("APPROVED", "PARTIALLY_RECEIVED")


def receive(db: Session, po_no: str, warehouse_code: str, requested: list[tuple[str, int]], actor: Actor) -> dict[str, Any]:
    order = purchase_orders.get_by_no(db, po_no, for_update=True)
    if order.status not in RECEIVABLE:
        raise ScmError(
            "INVALID_TRANSITION",
            f"PURCHASE_ORDER: penerimaan hanya untuk PO APPROVED atau PARTIALLY_RECEIVED, status sekarang {order.status}",
            409,
            {"machine": "PURCHASE_ORDER", "current": order.status, "requested": "RECEIVE", "allowed": list(RECEIVABLE)},
            po_no,
        )
    if db.get(Warehouse, warehouse_code) is None:
        raise ScmError(
            "UNKNOWN_WAREHOUSE", f"Gudang {warehouse_code} tidak dikenal", 422, {"warehouse_code": warehouse_code}, po_no
        )

    # Baca dengan kunci: `qty_received` harus nilai terbaru supaya dua penerimaan tidak melebihi pesanan.
    order_lines = {
        line.item_sku: line
        for line in db.query(PurchaseOrderLine)
        .filter(PurchaseOrderLine.purchase_order_id == order.id)
        .with_for_update()
        .populate_existing()
        .all()
    }
    seen: set[str] = set()
    for sku, qty in requested:  # periksa semua baris sebelum ada yang berubah
        if sku in seen:
            raise ScmError("DUPLICATE_LINE", f"Barang {sku} muncul lebih dari sekali", 422, {"item_sku": sku}, po_no)
        seen.add(sku)
        line = order_lines.get(sku)
        if line is None:
            raise ScmError("ITEM_NOT_IN_PO", f"Barang {sku} tidak ada di {po_no}", 422, {"item_sku": sku}, po_no)
        remaining = line.qty - line.qty_received
        if qty > remaining:
            raise ScmError(
                "OVER_RECEIPT",
                f"Penerimaan {sku} melebihi sisa pesanan",
                409,
                {"item_sku": sku, "requested": qty, "remaining": remaining},
                po_no,
            )

    receipt = GoodsReceipt(
        gr_no=new_goods_receipt_no(db),
        po_no=po_no,
        warehouse_code=warehouse_code,
        received_by=actor.sub,
        received_at=clock.utcnow(),
    )
    serial_numbers: list[str] = []
    for sku, qty in requested:
        ledger.receive(
            db, warehouse_code=warehouse_code, item_sku=sku, qty=qty,
            ref_type="GOODS_RECEIPT", ref_no=receipt.gr_no, correlation_id=po_no, actor=actor,
        )
        serials: list[str] = []
        if db.get(Item, sku).is_serialized:
            serials = ports.assets.register_units(
                db, item_sku=sku, warehouse_code=warehouse_code, qty=qty, gr_no=receipt.gr_no
            )
            serial_numbers += serials
        order_lines[sku].qty_received += qty
        receipt.lines.append(
            GoodsReceiptLine(item_sku=sku, qty=qty, serial_numbers=json.dumps(serials) if serials else None)
        )
    db.add(receipt)

    complete = all(line.qty_received >= line.qty for line in order_lines.values())
    new_status = "RECEIVED" if complete else "PARTIALLY_RECEIVED"
    if new_status != order.status:
        purchase_orders.transition(order, new_status)
    else:
        order.version = (order.version or 1) + 1
    audit.record(
        db, actor, "purchase_order.receive", purchase_orders.ENTITY, po_no,
        {"gr_no": receipt.gr_no, "warehouse_code": warehouse_code, "lines": dict(requested)}, po_no,
    )
    db.flush()

    # Barang sudah masuk saldo: tawarkan ke permintaan barang yang menunggu.
    for sku, _ in requested:
        ports.stock_requests.reevaluate_pending(db, item_sku=sku, warehouse_code=warehouse_code)

    return {"gr_no": receipt.gr_no, "po_status": order.status, "serial_numbers": serial_numbers}

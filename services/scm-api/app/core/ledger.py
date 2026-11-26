"""Buku besar stok: satu-satunya tempat saldo `InventoryBalance` boleh berubah (spec 4.1).

Setiap operasi berjalan di transaksi pemanggil (tanpa commit), mengunci baris saldo
(`SELECT ... FOR UPDATE` di MySQL), menaikkan `version` (kunci optimistik lewat `version_id_col`),
dan menulis tepat satu `StockMovement`.

    qty_available = qty_physical - qty_reserved - qty_damaged
"""
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.auth import Actor
from app.core.errors import ScmError
from app.core.models import InventoryBalance, Item, StockMovement, Warehouse

RECEIVE = "RECEIVE"
RESERVE = "RESERVE"
RELEASE = "RELEASE"
ISSUE = "ISSUE"
ISSUE_EXTRA = "ISSUE_EXTRA"
RETURN_GOOD = "RETURN_GOOD"
RETURN_DAMAGED = "RETURN_DAMAGED"
MARK_DAMAGED = "MARK_DAMAGED"
WRITE_OFF = "WRITE_OFF"


def get_balance(db: Session, warehouse_code: str, item_sku: str) -> InventoryBalance | None:
    return (
        db.query(InventoryBalance)
        .filter(InventoryBalance.warehouse_code == warehouse_code, InventoryBalance.item_sku == item_sku)
        .first()
    )


def get_available(db: Session, warehouse_code: str, item_sku: str) -> int:
    balance = get_balance(db, warehouse_code, item_sku)
    return balance.qty_available if balance is not None else 0


def _check_qty(qty: int) -> None:
    if not isinstance(qty, int) or isinstance(qty, bool) or qty <= 0:
        raise ScmError("INVALID_QUANTITY", "Jumlah harus bilangan bulat lebih dari 0", 422, {"qty": qty})


def _lock(db: Session, warehouse_code: str, item_sku: str, create: bool) -> InventoryBalance | None:
    balance = (
        db.query(InventoryBalance)
        .filter(InventoryBalance.warehouse_code == warehouse_code, InventoryBalance.item_sku == item_sku)
        .with_for_update()
        .first()
    )
    if balance is not None or not create:
        return balance
    if db.get(Warehouse, warehouse_code) is None:
        raise ScmError("UNKNOWN_WAREHOUSE", f"Gudang {warehouse_code} tidak dikenal", 422, {"warehouse_code": warehouse_code})
    if db.get(Item, item_sku) is None:
        raise ScmError("UNKNOWN_ITEM", f"Barang {item_sku} tidak dikenal", 422, {"item_sku": item_sku})
    balance = InventoryBalance(warehouse_code=warehouse_code, item_sku=item_sku, qty_physical=0, qty_reserved=0, qty_damaged=0)
    db.add(balance)
    db.flush()
    return balance


def _insufficient(balance: InventoryBalance | None, warehouse_code: str, item_sku: str, qty: int) -> ScmError:
    available = balance.qty_available if balance is not None else 0
    return ScmError(
        "INSUFFICIENT_STOCK",
        f"Stok {item_sku} di gudang {warehouse_code} tidak cukup",
        409,
        {"sku": item_sku, "warehouse_code": warehouse_code, "requested": qty, "available": available},
    )


def _mismatch(code: str, message: str, item_sku: str, qty: int, held: int) -> ScmError:
    return ScmError(code, message, 409, {"sku": item_sku, "requested": qty, "held": held})


def _record(
    db: Session,
    balance: InventoryBalance,
    movement_type: str,
    qty: int,
    ref_type: str,
    ref_no: str,
    correlation_id: str | None,
    actor: Actor | str | None,
) -> StockMovement:
    movement = StockMovement(
        warehouse_code=balance.warehouse_code,
        item_sku=balance.item_sku,
        type=movement_type,
        qty=qty,
        ref_type=ref_type,
        ref_no=ref_no,
        correlation_id=correlation_id,
        created_by=actor.sub if isinstance(actor, Actor) else actor,
    )
    db.add(movement)
    try:
        db.flush()
    except StaleDataError as exc:
        raise ScmError("CONCURRENT_UPDATE", "Saldo stok diubah permintaan lain, coba lagi", 409) from exc
    return movement


def _apply(
    db: Session,
    *,
    kind: str,
    warehouse_code: str,
    item_sku: str,
    qty: int,
    ref_type: str,
    ref_no: str,
    correlation_id: str | None,
    actor: Actor | str | None,
    create: bool = False,
) -> StockMovement:
    _check_qty(qty)
    balance = _lock(db, warehouse_code, item_sku, create)
    available = balance.qty_available if balance is not None else 0

    if kind == RECEIVE or kind == RETURN_GOOD:
        balance.qty_physical += qty
    elif kind == RETURN_DAMAGED:
        balance.qty_physical += qty
        balance.qty_damaged += qty
    elif kind == RESERVE:
        if balance is None or available < qty:
            raise _insufficient(balance, warehouse_code, item_sku, qty)
        balance.qty_reserved += qty
    elif kind == RELEASE:
        held = balance.qty_reserved if balance is not None else 0
        if held < qty:
            raise _mismatch("RESERVATION_MISMATCH", f"Reservasi {item_sku} kurang dari yang dilepas", item_sku, qty, held)
        balance.qty_reserved -= qty
    elif kind == ISSUE:
        held = balance.qty_reserved if balance is not None else 0
        if held < qty:
            raise _mismatch("RESERVATION_MISMATCH", f"Barang {item_sku} belum direservasi sebanyak itu", item_sku, qty, held)
        if balance.qty_physical < qty:
            raise _insufficient(balance, warehouse_code, item_sku, qty)
        balance.qty_physical -= qty
        balance.qty_reserved -= qty
    elif kind == ISSUE_EXTRA:
        if balance is None or available < qty:
            raise _insufficient(balance, warehouse_code, item_sku, qty)
        balance.qty_physical -= qty
    elif kind == MARK_DAMAGED:
        if balance is None or available < qty:
            raise _insufficient(balance, warehouse_code, item_sku, qty)
        balance.qty_damaged += qty
    elif kind == WRITE_OFF:
        held = balance.qty_damaged if balance is not None else 0
        if held < qty:
            raise _mismatch("DAMAGED_MISMATCH", f"Stok rusak {item_sku} kurang dari yang dihapus buku", item_sku, qty, held)
        balance.qty_physical -= qty
        balance.qty_damaged -= qty
    else:  # pragma: no cover - dijaga oleh fungsi publik di bawah
        raise ValueError(kind)

    return _record(db, balance, kind, qty, ref_type, ref_no, correlation_id, actor)


def _op(kind: str, create: bool = False):
    def operation(
        db: Session,
        *,
        warehouse_code: str,
        item_sku: str,
        qty: int,
        ref_type: str,
        ref_no: str,
        correlation_id: str | None = None,
        actor: Actor | str | None = None,
    ) -> StockMovement:
        return _apply(
            db,
            kind=kind,
            warehouse_code=warehouse_code,
            item_sku=item_sku,
            qty=qty,
            ref_type=ref_type,
            ref_no=ref_no,
            correlation_id=correlation_id,
            actor=actor,
            create=create,
        )

    operation.__name__ = kind.lower()
    return operation


receive = _op(RECEIVE, create=True)
reserve = _op(RESERVE)
release = _op(RELEASE)
issue = _op(ISSUE)
issue_extra = _op(ISSUE_EXTRA)
return_good = _op(RETURN_GOOD, create=True)
return_damaged = _op(RETURN_DAMAGED, create=True)
mark_damaged = _op(MARK_DAMAGED)
write_off = _op(WRITE_OFF)

__all__: list[Any] = [
    "get_balance",
    "get_available",
    "receive",
    "reserve",
    "release",
    "issue",
    "issue_extra",
    "return_good",
    "return_damaged",
    "mark_damaged",
    "write_off",
]

"""Kode bisnis SCM dari sequence database (`shared.ids.next_code`), bukan `count()+1`."""
from sqlalchemy.orm import Session

from shared.ids import next_code

from app.core import clock
from app.core.models import IdCounter


def _yearly(db: Session, prefix: str, width: int) -> str:
    year = clock.current_year()
    return next_code(db, IdCounter, f"{prefix}:{year}", f"{prefix}-{year}-{{n:0{width}d}}")


def new_stock_request_no(db: Session) -> str:
    return _yearly(db, "SR", 6)


def new_purchase_request_no(db: Session) -> str:
    return _yearly(db, "PR", 4)


def new_purchase_order_no(db: Session) -> str:
    return _yearly(db, "PO", 4)


def new_goods_receipt_no(db: Session) -> str:
    return _yearly(db, "GR", 4)


def new_transfer_no(db: Session) -> str:
    return _yearly(db, "TRF", 4)


def new_serial_number(db: Session) -> str:
    year = clock.current_year()
    return next_code(db, IdCounter, f"SN-ONT:{year}", f"SN-ONT-{year}-{{n:06d}}")


def new_vendor_code(db: Session) -> str:
    return next_code(db, IdCounter, "VEN", "VEN-{n:04d}")


def new_lot_seq(db: Session) -> int:
    """Urutan masuk batch stok (naik terus; dasar FIFO)."""
    return int(next_code(db, IdCounter, "LOT", "{n}"))

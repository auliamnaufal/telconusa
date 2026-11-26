"""Pekerjaan berkala Slice A."""
from sqlalchemy.orm import Session

from app.core.jobs import job
from app.stock import service


@job("stock.expire_reservations", interval_seconds=60)
def expire_reservations(db: Session) -> list[str]:
    """Lepas reservasi permintaan barang yang lewat 72 jam (spec F7)."""
    return service.expire_due(db)

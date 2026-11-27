"""Pekerjaan berkala Slice B."""
from sqlalchemy.orm import Session

from app.core.jobs import job
from app.procurement import purchase_requests


@job("procurement.check_budgets", interval_seconds=30)
def check_budgets(db: Session) -> list[str]:
    """Periksa anggaran PR `PENDING_BUDGET` ke Finance (spec F8.1)."""
    return purchase_requests.check_pending_budgets(db)

"""Handler event masuk Slice A (CRM -> SCM)."""
from typing import Any

from sqlalchemy.orm import Session

from app.core.events import handler
from app.stock import service


@handler("ticket.created")
def on_ticket_created(db: Session, envelope: dict[str, Any]) -> None:
    service.create_from_ticket(db, envelope.get("data") or {}, envelope.get("correlation_id"))


@handler("ticket.assigned")
def on_ticket_assigned(db: Session, envelope: dict[str, Any]) -> None:
    service.apply_assignment(db, envelope.get("data") or {})


@handler("ticket.items_reported")
def on_ticket_items_reported(db: Session, envelope: dict[str, Any]) -> None:
    service.report_items(db, envelope.get("data") or {})

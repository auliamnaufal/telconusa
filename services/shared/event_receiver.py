import inspect
import json
import logging
from typing import Any, Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import DateTime, String, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from shared.events import verify_signature

logger = logging.getLogger("telconusa.event_receiver")


def verify_event_request(raw_body: bytes, signature: str | None) -> None:
    """Reject the request unless a valid HMAC signature is present."""
    if not verify_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Signature event tidak valid atau tidak ada")


def make_processed_event_model(Base: type) -> type:
    class ProcessedEvent(Base):
        __tablename__ = "processed_events"

        event_id: Mapped[str] = mapped_column(String(40), primary_key=True)
        event_type: Mapped[str] = mapped_column(String(60), nullable=False)
        processed_at = mapped_column(DateTime, server_default=func.now())

    return ProcessedEvent


def _parse_envelope(raw_body: bytes) -> dict[str, Any]:
    try:
        event = json.loads(raw_body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Body event bukan JSON yang valid") from exc
    if not isinstance(event, dict) or not event.get("event_id") or not event.get("event_type"):
        raise HTTPException(status_code=400, detail="Envelope event harus memiliki event_id dan event_type")
    return event


def create_events_router(get_db: Callable, ProcessedEvent: type, handlers: dict[str, Callable]) -> APIRouter:
    router = APIRouter()

    @router.post("/internal/events")
    async def receive_event(
        request: Request,
        x_telconusa_signature: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> dict[str, str]:
        raw_body = await request.body()
        verify_event_request(raw_body, x_telconusa_signature)
        event = _parse_envelope(raw_body)
        event_id, event_type = event["event_id"], event["event_type"]

        if db.get(ProcessedEvent, event_id) is not None:
            return {"status": "duplicate_ignored"}

        handler = handlers.get(event_type)
        try:
            if handler is not None:
                result = handler(db, event)
                if inspect.isawaitable(result):
                    await result
            db.add(ProcessedEvent(event_id=event_id, event_type=event_type))
            db.commit()
        except IntegrityError:
            db.rollback()
            return {"status": "duplicate_ignored"}
        except Exception:
            db.rollback()
            logger.exception("Handler for %s (%s) failed", event_type, event_id)
            raise

        status = "processed" if handler is not None else "ignored"
        return {"status": status, "event_id": event_id}

    return router

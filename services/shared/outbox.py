import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from shared import events

logger = logging.getLogger("telconusa.outbox")

STATUS_PENDING = "PENDING"
STATUS_SENT = "SENT"
BATCH_SIZE = 50
RETRY_DELAYS = (timedelta(minutes=1), timedelta(minutes=5), timedelta(minutes=15))
MAX_ATTEMPTS = len(RETRY_DELAYS) + 1


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def make_outbox_models(Base: type) -> tuple[type, type]:
    class OutboxEvent(Base):
        __tablename__ = "outbox_events"

        id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        event_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
        event_type: Mapped[str] = mapped_column(String(60), nullable=False)
        correlation_id: Mapped[str] = mapped_column(String(40), nullable=False)
        source: Mapped[str] = mapped_column(String(20), nullable=False)
        payload_json: Mapped[str] = mapped_column(Text, nullable=False)
        status: Mapped[str] = mapped_column(String(16), nullable=False, default=STATUS_PENDING)
        attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        next_attempt_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
        last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    class DeadLetterEvent(Base):
        __tablename__ = "dead_letter_events"

        id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        event_id: Mapped[str] = mapped_column(String(40), nullable=False)
        event_type: Mapped[str] = mapped_column(String(60), nullable=False)
        correlation_id: Mapped[str] = mapped_column(String(40), nullable=False)
        source: Mapped[str] = mapped_column(String(20), nullable=False)
        payload_json: Mapped[str] = mapped_column(Text, nullable=False)
        attempts: Mapped[int] = mapped_column(Integer, nullable=False)
        last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
        dead_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)

    return OutboxEvent, DeadLetterEvent


def enqueue_event(
    db: Session,
    Outbox: type,
    event_type: str,
    correlation_id: str,
    data: dict[str, Any],
    source: str,
) -> str:
    """Add a PENDING outbox row to the caller's session; the caller commits it with its own changes."""
    event_id = f"evt_{uuid.uuid4().hex[:12].upper()}"
    db.add(
        Outbox(
            event_id=event_id,
            event_type=event_type,
            correlation_id=correlation_id,
            source=source,
            payload_json=json.dumps(data, default=str),
            status=STATUS_PENDING,
            attempts=0,
            next_attempt_at=_utcnow(),
        )
    )
    return event_id


async def _deliver_row(row: Any) -> tuple[bool, str | None]:
    targets = events.EVENT_SUBSCRIBERS.get(row.event_type, [])
    if not targets:
        return True, None
    envelope = events.build_envelope(
        row.event_type,
        row.source,
        row.correlation_id,
        json.loads(row.payload_json),
        event_id=row.event_id,
    )
    try:
        ok = await events.deliver(envelope, targets)
    except Exception as exc:
        return False, str(exc)
    return ok, None if ok else "delivery failed for at least one subscriber"


def _move_to_dead_letter(db: Session, DeadLetter: type, row: Any, now: datetime) -> None:
    db.add(
        DeadLetter(
            event_id=row.event_id,
            event_type=row.event_type,
            correlation_id=row.correlation_id,
            source=row.source,
            payload_json=row.payload_json,
            attempts=row.attempts,
            last_error=row.last_error,
            dead_at=now,
        )
    )
    db.delete(row)


def _record_failure(db: Session, DeadLetter: type, row: Any, error: str | None, now: datetime) -> None:
    row.attempts += 1
    row.last_error = error
    if row.attempts >= MAX_ATTEMPTS:
        _move_to_dead_letter(db, DeadLetter, row, now)
    else:
        row.next_attempt_at = now + RETRY_DELAYS[row.attempts - 1]


async def relay_once(
    session_factory: Callable[[], Session],
    Outbox: type,
    DeadLetter: type,
    now: datetime | None = None,
) -> int:
    """Deliver due PENDING events once; returns how many were marked SENT."""
    now = now or _utcnow()
    sent = 0
    db = session_factory()
    try:
        rows = (
            db.query(Outbox)
            .filter(Outbox.status == STATUS_PENDING, Outbox.next_attempt_at <= now)
            .order_by(Outbox.created_at, Outbox.id)
            .limit(BATCH_SIZE)
            .all()
        )
        for row in rows:
            ok, error = await _deliver_row(row)
            if ok:
                row.status = STATUS_SENT
                row.last_error = None
                sent += 1
            else:
                _record_failure(db, DeadLetter, row, error, now)
            db.commit()
    finally:
        db.close()
    return sent


async def run_relay(
    session_factory: Callable[[], Session],
    Outbox: type,
    DeadLetter: type,
    interval_seconds: float = 5.0,
) -> None:
    while True:
        try:
            await relay_once(session_factory, Outbox, DeadLetter)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Outbox relay iteration failed")
        await asyncio.sleep(interval_seconds)

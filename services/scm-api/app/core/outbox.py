"""Penerbitan event lewat outbox (`shared.outbox`)."""
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from sqlalchemy.orm import Session

from shared.outbox import enqueue_event, run_relay

from app.core.models import DeadLetterEvent, OutboxEvent
from app.database import SessionLocal

SOURCE = "scm"


def publish(db: Session, event_type: str, correlation_id: str, data: dict[str, Any]) -> str:
    """Tambah baris outbox PENDING ke transaksi pemanggil; commit bersama perubahan datanya.

    Hanya event yang sudah ada di `contracts/events/` yang boleh diterbitkan.
    """
    return enqueue_event(db, OutboxEvent, event_type, correlation_id, data, SOURCE)


@asynccontextmanager
async def relay_lifespan(_: FastAPI):
    relay = asyncio.create_task(run_relay(SessionLocal, OutboxEvent, DeadLetterEvent))
    try:
        yield
    finally:
        relay.cancel()
        try:
            await relay
        except asyncio.CancelledError:
            pass

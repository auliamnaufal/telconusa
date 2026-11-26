"""Penerima event masuk SCM.

Handler didaftarkan dengan `@handler("ticket.created")` di `app/<slice>/events.py`. Penerima
(`shared.event_receiver`) menolak event tanpa tanda tangan (401), mengabaikan `event_id` yang
sudah diproses, dan menjalankan handler dalam transaksi yang sama dengan pencatatan `event_id`.
Handler menerima `(db, envelope)`; ia tidak melakukan commit.
"""
from typing import Any, Callable

from sqlalchemy.orm import Session

from shared.event_receiver import create_events_router

from app.core.models import ProcessedEvent
from app.database import get_db

EventHandler = Callable[[Session, dict[str, Any]], Any]

HANDLERS: dict[str, EventHandler] = {}


def handler(event_type: str) -> Callable[[EventHandler], EventHandler]:
    def _register(fn: EventHandler) -> EventHandler:
        if event_type in HANDLERS:
            raise RuntimeError(f"Handler untuk event {event_type} sudah terdaftar")
        HANDLERS[event_type] = fn
        return fn

    return _register


events_router = create_events_router(get_db, ProcessedEvent, HANDLERS)

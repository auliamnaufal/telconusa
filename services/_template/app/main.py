import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from shared.auth import EMPLOYEE_ROLES, require_roles
from shared.config import settings
from shared.event_receiver import create_events_router
from shared.outbox import run_relay
from shared.schemas import HealthResponse, now_wib_iso
from shared.service_auth import require_service

from app.database import SessionLocal, get_db
from app.models import DeadLetterEvent, Example, OutboxEvent, ProcessedEvent


def handle_example_event(db: Session, envelope: dict[str, Any]) -> None:
    """Contoh handler event masuk; dipanggil sekali per event_id (idempotent)."""
    db.add(Example(name=f"from {envelope['event_type']}"))


EVENT_HANDLERS = {"example.happened": handle_example_event}


@asynccontextmanager
async def lifespan(_: FastAPI):
    relay = asyncio.create_task(run_relay(SessionLocal, OutboxEvent, DeadLetterEvent))
    try:
        yield
    finally:
        relay.cancel()
        try:
            await relay
        except asyncio.CancelledError:
            pass


app = FastAPI(title="TelcoNusa __NAME__ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_events_router(get_db, ProcessedEvent, EVENT_HANDLERS))


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="__NAME__-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())


@app.get("/api/v1/examples")
def list_examples(
    _: dict = Depends(require_roles(*EMPLOYEE_ROLES)),
    db: Session = Depends(get_db),
):
    return [{"id": e.id, "name": e.name} for e in db.query(Example).all()]


@app.get("/api/v1/examples/internal")
def list_examples_internal(
    _: dict = Depends(require_service("example:read")),
    db: Session = Depends(get_db),
):
    return [{"id": e.id, "name": e.name} for e in db.query(Example).all()]

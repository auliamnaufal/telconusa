from datetime import datetime, timedelta, timezone
from typing import Any
from pydantic import BaseModel

WIB = timezone(timedelta(hours=7))


def now_wib_iso() -> str:
    return datetime.now(WIB).isoformat(timespec="seconds")


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    version: int = 1
    occurred_at: str
    source: str
    correlation_id: str
    data: dict[str, Any]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    transport: str
    timestamp: str

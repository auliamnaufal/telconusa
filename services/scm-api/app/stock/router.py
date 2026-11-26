"""Endpoint HTTP Slice A: permintaan barang (`contracts/openapi/scm.yaml`)."""
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import ROLES_WAREHOUSE, Actor, require_scm_roles
from app.core.idempotency import idempotency_key, run_idempotent
from app.database import get_db
from app.stock import service

router = APIRouter(prefix="/api/v1", tags=["stock-requests"])


class IssueLineBody(BaseModel):
    item_sku: str
    qty: int = Field(gt=0)
    serial_numbers: list[str] | None = None


class IssueBody(BaseModel):
    lines: list[IssueLineBody] = Field(min_length=1)


class ExtraLineBody(BaseModel):
    item_sku: str
    qty: int = Field(gt=0)


class IssueExtraBody(BaseModel):
    lines: list[ExtraLineBody] = Field(min_length=1)


class FlagDamagedBody(BaseModel):
    item_sku: str
    qty: int = Field(gt=0)
    serial_number: str | None = None
    notes: str | None = None


class CancelBody(BaseModel):
    reason: str = Field(min_length=1)


def _idempotent(db: Session, key: str | None, endpoint: str, action) -> JSONResponse:
    status, payload = run_idempotent(db, key, endpoint, action)
    return JSONResponse(content=payload, status_code=status)


@router.get("/stock-requests")
def list_stock_requests(
    response: Response,
    status: str | None = None,
    city_code: str | None = None,
    ticket_code: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = service.list_requests(db, status, city_code, ticket_code, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [service.to_summary(row) for row in rows]


@router.get("/stock-requests/{stock_request_no}")
def get_stock_request(
    stock_request_no: str,
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return service.to_detail(service.get_by_no(db, stock_request_no))


@router.post("/stock-requests/{stock_request_no}/issue")
def issue_stock_request(
    stock_request_no: str,
    body: IssueBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_WAREHOUSE)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    lines = [service.IssueLine(line.item_sku, line.qty, line.serial_numbers) for line in body.lines]
    return _idempotent(
        db, key, f"POST /api/v1/stock-requests/{stock_request_no}/issue",
        lambda: (200, service.issue(db, stock_request_no, lines, actor)),
    )


@router.post("/stock-requests/{stock_request_no}/issue-extra")
def issue_extra_items(
    stock_request_no: str,
    body: IssueExtraBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_WAREHOUSE)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    lines = [(line.item_sku, line.qty) for line in body.lines]
    return _idempotent(
        db, key, f"POST /api/v1/stock-requests/{stock_request_no}/issue-extra",
        lambda: (200, service.issue_extra(db, stock_request_no, lines, actor)),
    )


@router.post("/stock-requests/{stock_request_no}/flag-damaged")
def flag_damaged_item(
    stock_request_no: str,
    body: FlagDamagedBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_WAREHOUSE)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/stock-requests/{stock_request_no}/flag-damaged",
        lambda: (
            200,
            service.flag_damaged(db, stock_request_no, body.item_sku, body.qty, body.serial_number, body.notes, actor),
        ),
    )


@router.post("/stock-requests/{stock_request_no}/cancel")
def cancel_stock_request(
    stock_request_no: str,
    body: CancelBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_WAREHOUSE)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/stock-requests/{stock_request_no}/cancel",
        lambda: (200, service.cancel(db, stock_request_no, body.reason, actor)),
    )

"""Endpoint HTTP Slice B: PR, PO, persetujuan, penerimaan barang."""
from typing import Any, Callable

from fastapi import APIRouter, Depends, Header, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    ROLES_APPROVER,
    ROLES_PO_READ,
    ROLES_PROCUREMENT,
    ROLES_WAREHOUSE,
    Actor,
    require_scm_roles,
)
from app.core.idempotency import idempotency_key, run_idempotent
from app.core.outbox import SOURCE
from app.database import get_db
from app.procurement import purchase_orders, purchase_requests, receipts

router = APIRouter(prefix="/api/v1", tags=["procurement"])

MAX_QTY = 2_147_483_647  # batas kolom INTEGER
MAX_PRICE = 1_000_000_000_000


class CreatePoBody(BaseModel):
    vendor_code: str
    item_sku: str
    qty: int = Field(gt=0, le=MAX_QTY)


class UnitPriceBody(BaseModel):
    item_sku: str
    unit_price: int = Field(gt=0, le=MAX_PRICE)


class CreatePoFromRequestBody(BaseModel):
    vendor_code: str
    unit_prices: list[UnitPriceBody] = Field(min_length=1)


class DecisionBody(BaseModel):
    comment: str | None = None


class QuoteBody(BaseModel):
    vendor_code: str
    unit_price: int = Field(gt=0, le=MAX_PRICE)
    notes: str | None = None


class ReceiptLineBody(BaseModel):
    item_sku: str
    qty: int = Field(gt=0, le=MAX_QTY)


class ReceiptBody(BaseModel):
    warehouse_code: str
    lines: list[ReceiptLineBody] = Field(min_length=1)


def correlation_header(x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id")) -> str:
    return x_correlation_id or f"{SOURCE}-procurement"


def _idempotent(db: Session, key: str | None, endpoint: str, status: int, action: Callable[[], dict[str, Any]]) -> JSONResponse:
    code, payload = run_idempotent(db, key, endpoint, lambda: (status, action()))
    return JSONResponse(content=payload, status_code=code)


@router.get("/purchase-requests")
def list_purchase_requests(
    response: Response,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = purchase_requests.list_requests(db, status, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [purchase_requests.to_summary(row) for row in rows]


@router.get("/purchase-requests/{purchase_request_no}")
def get_purchase_request(
    purchase_request_no: str,
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return purchase_requests.to_detail(db, purchase_requests.get_by_no(db, purchase_request_no))


@router.post("/purchase-requests/{purchase_request_no}/create-po", status_code=201)
def create_po_from_request(
    purchase_request_no: str,
    body: CreatePoFromRequestBody,
    key: str | None = Depends(idempotency_key),
    correlation_id: str = Depends(correlation_header),
    actor: Actor = Depends(require_scm_roles(*ROLES_PROCUREMENT)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    prices = [(line.item_sku, line.unit_price) for line in body.unit_prices]
    return _idempotent(
        db, key, f"POST /api/v1/purchase-requests/{purchase_request_no}/create-po", 201,
        lambda: purchase_orders.create_from_request(
            db, purchase_request_no, body.vendor_code, prices, actor, correlation_id
        ),
    )


@router.post("/purchase-orders", status_code=201)
def create_purchase_order(
    body: CreatePoBody,
    key: str | None = Depends(idempotency_key),
    correlation_id: str = Depends(correlation_header),
    actor: Actor = Depends(require_scm_roles(*ROLES_PROCUREMENT)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, "POST /api/v1/purchase-orders", 201,
        lambda: purchase_orders.create_direct(db, body.vendor_code, body.item_sku, body.qty, actor, correlation_id),
    )


@router.get("/purchase-orders")
def list_purchase_orders(
    response: Response,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles(*ROLES_PO_READ)),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = purchase_orders.list_orders(db, status, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [purchase_orders.to_summary(row) for row in rows]


@router.get("/purchase-orders/{po_no}")
def get_purchase_order(
    po_no: str,
    _: Actor = Depends(require_scm_roles(*ROLES_PO_READ)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return purchase_orders.to_detail(db, purchase_orders.get_by_no(db, po_no))


@router.post("/purchase-orders/{po_no}/quotes", status_code=201)
def add_purchase_order_quote(
    po_no: str,
    body: QuoteBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_PROCUREMENT)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/purchase-orders/{po_no}/quotes", 201,
        lambda: purchase_orders.add_quote(db, po_no, body.vendor_code, body.unit_price, body.notes, actor),
    )


@router.post("/purchase-orders/{po_no}/submit")
def submit_purchase_order(
    po_no: str,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_PROCUREMENT)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/purchase-orders/{po_no}/submit", 200,
        lambda: purchase_orders.submit(db, po_no, actor),
    )


@router.post("/purchase-orders/{po_no}/approve")
def approve_purchase_order(
    po_no: str,
    body: DecisionBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_APPROVER)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/purchase-orders/{po_no}/approve", 200,
        lambda: purchase_orders.decide(db, po_no, "APPROVED", body.comment, actor),
    )


@router.post("/purchase-orders/{po_no}/reject")
def reject_purchase_order(
    po_no: str,
    body: DecisionBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_APPROVER)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    return _idempotent(
        db, key, f"POST /api/v1/purchase-orders/{po_no}/reject", 200,
        lambda: purchase_orders.decide(db, po_no, "REJECTED", body.comment, actor),
    )


@router.post("/purchase-orders/{po_no}/receipts", status_code=201)
def receive_goods(
    po_no: str,
    body: ReceiptBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_WAREHOUSE)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    lines = [(line.item_sku, line.qty) for line in body.lines]
    return _idempotent(
        db, key, f"POST /api/v1/purchase-orders/{po_no}/receipts", 201,
        lambda: receipts.receive(db, po_no, body.warehouse_code, lines, actor),
    )

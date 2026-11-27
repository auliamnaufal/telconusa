"""Endpoint HTTP Slice D.

Data master (SCM-D-01) dan pengelolaan paket (SCM-D-02) berstatus DRAFT di `tracks/scm/contract-extension.md`;
`GET /package-kits/{sku}` ada di `contracts/openapi/scm.yaml`.
"""
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.catalog import service
from app.core.auth import ROLES_MANAGER, Actor, require_scm_roles, require_scope
from app.core.idempotency import idempotency_key, run_idempotent
from app.database import get_db

router = APIRouter(prefix="/api/v1", tags=["catalog"])


class ItemCreateBody(BaseModel):
    sku: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z0-9-]+$")
    name: str = Field(min_length=1, max_length=120)
    unit: str = Field(min_length=1, max_length=16)
    unit_cost: int = Field(ge=0)
    reorder_point: int = Field(100, ge=0)
    safety_stock: int = Field(50, ge=0)
    is_serialized: bool = False
    specification: str | None = None


class ItemUpdateBody(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    unit: str | None = Field(None, min_length=1, max_length=16)
    unit_cost: int | None = Field(None, ge=0)
    reorder_point: int | None = Field(None, ge=0)
    safety_stock: int | None = Field(None, ge=0)
    is_serialized: bool | None = None
    specification: str | None = None


class VendorCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=40)
    rating_score: Decimal = Field(Decimal("0"), ge=0, le=5, decimal_places=2)


class VendorUpdateBody(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    category: str | None = Field(None, min_length=1, max_length=40)
    rating_score: Decimal | None = Field(None, ge=0, le=5, decimal_places=2)


class KitLineBody(BaseModel):
    item_sku: str = Field(min_length=1)
    qty: int = Field(gt=0)


class KitReplaceBody(BaseModel):
    lines: list[KitLineBody] = Field(min_length=1)


def _changes(body: BaseModel) -> dict[str, Any]:
    """Hanya bidang yang dikirim; `null` eksplisit diabaikan kecuali `specification`."""
    sent = body.model_dump(exclude_unset=True)
    return {k: v for k, v in sent.items() if v is not None or k == "specification"}


# ---------------------------------------------------------------------------- barang


@router.get("/items")
def list_items(
    response: Response,
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = service.list_items(db, q, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [service.item_to_dict(row) for row in rows]


@router.post("/items")
def create_item(
    body: ItemCreateBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_MANAGER)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    status, payload = run_idempotent(
        db, key, "POST /api/v1/items", lambda: (201, service.create_item(db, body.model_dump(), actor))
    )
    return JSONResponse(content=payload, status_code=status)


@router.patch("/items/{sku}")
def update_item(
    sku: str,
    body: ItemUpdateBody,
    actor: Actor = Depends(require_scm_roles(*ROLES_MANAGER)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = service.update_item(db, sku, _changes(body), actor)
    db.commit()
    return result


# ---------------------------------------------------------------------------- gudang


@router.get("/warehouses")
def list_warehouses(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = service.list_warehouses(db, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [service.warehouse_to_dict(row) for row in rows]


# ---------------------------------------------------------------------------- vendor


@router.get("/vendors")
def list_vendors(
    response: Response,
    category: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = service.list_vendors(db, category, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [service.vendor_to_dict(row) for row in rows]


@router.post("/vendors")
def create_vendor(
    body: VendorCreateBody,
    key: str | None = Depends(idempotency_key),
    actor: Actor = Depends(require_scm_roles(*ROLES_MANAGER)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    status, payload = run_idempotent(
        db, key, "POST /api/v1/vendors", lambda: (201, service.create_vendor(db, body.model_dump(), actor))
    )
    return JSONResponse(content=payload, status_code=status)


@router.patch("/vendors/{code}")
def update_vendor(
    code: str,
    body: VendorUpdateBody,
    actor: Actor = Depends(require_scm_roles(*ROLES_MANAGER)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = service.update_vendor(db, code, _changes(body), actor)
    db.commit()
    return result


# ---------------------------------------------------------------------------- paket


@router.get("/package-kits")
def list_package_kits(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: Actor = Depends(require_scm_roles()),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows, total = service.list_kits(db, page, limit)
    response.headers["X-Total-Count"] = str(total)
    return [service.kit_to_dict(db, row) for row in rows]


@router.get("/package-kits/{sku}")
def get_package_kit(
    sku: str,
    _: dict = Depends(require_scope("packagekits:read")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return service.kit_to_dict(db, service.get_kit(db, sku))


@router.put("/package-kits/{sku}")
def replace_package_kit(
    sku: str,
    body: KitReplaceBody,
    actor: Actor = Depends(require_scm_roles(*ROLES_MANAGER)),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = service.replace_kit(db, sku, [(line.item_sku, line.qty) for line in body.lines], actor)
    db.commit()
    return result

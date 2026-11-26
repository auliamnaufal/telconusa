"""Logika bisnis Slice A: permintaan barang, reservasi, pengeluaran, laporan pemakaian.

Semua fungsi berjalan di transaksi pemanggil dan tidak melakukan commit. Saldo hanya berubah lewat
`app.core.ledger`; status unit serial hanya lewat `ports.assets`; PR lewat `ports.procurement`.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core import audit, clock, ledger, machines
from app.core.auth import Actor
from app.core.codes import new_stock_request_no
from app.core.errors import ScmError
from app.core.models import Item, Warehouse
from app.core.outbox import publish
from app.core.ports import Shortage, ports
from app.stock.models import PendingAssignment, StockRequest, StockRequestLine

logger = logging.getLogger("telconusa.scm.stock")

RESERVATION_HOURS = 72
REF_TYPE = "STOCK_REQUEST"
SYSTEM_ACTOR = "system"


# ---------------------------------------------------------------------------- pembacaan


def get_by_no(db: Session, stock_request_no: str, for_update: bool = False) -> StockRequest:
    query = db.query(StockRequest).filter(StockRequest.stock_request_no == stock_request_no)
    if for_update:
        query = query.with_for_update()
    request = query.first()
    if request is None:
        raise ScmError(
            "STOCK_REQUEST_NOT_FOUND",
            f"Permintaan barang {stock_request_no} tidak ditemukan",
            404,
            {"stock_request_no": stock_request_no},
        )
    return request


def list_requests(
    db: Session,
    status: str | None = None,
    city_code: str | None = None,
    ticket_code: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[StockRequest], int]:
    query = db.query(StockRequest)
    if status:
        query = query.filter(StockRequest.status == status)
    if city_code:
        query = query.filter(StockRequest.city_code == city_code)
    if ticket_code:
        query = query.filter(StockRequest.ticket_code == ticket_code)
    total = query.count()
    rows = query.order_by(StockRequest.created_at.desc(), StockRequest.stock_request_no.desc()).offset((page - 1) * limit).limit(limit).all()
    return rows, total


def is_return_pending(request: StockRequest) -> bool:
    """Sudah dikeluarkan tetapi laporan pemakaian teknisi belum diproses."""
    return request.status == "ISSUED"


def to_summary(request: StockRequest) -> dict[str, Any]:
    return {
        "stock_request_no": request.stock_request_no,
        "ticket_code": request.ticket_code,
        "status": request.status,
        "technician_employee_id": request.technician_employee_id,
        "city_code": request.city_code,
        "return_pending": is_return_pending(request),
    }


def to_detail(request: StockRequest) -> dict[str, Any]:
    return {
        **to_summary(request),
        "warehouse_code": request.warehouse_code,
        "reserved_until": clock.to_wib_iso(request.reserved_until),
        "purchase_request_no": request.purchase_request_no,
        "discrepancy": bool(request.discrepancy),
        "cancel_reason": request.cancel_reason,
        "lines": [
            {
                "item_sku": line.item_sku,
                "qty_required": line.qty_required,
                "qty_issued": line.qty_issued,
                "qty_used": line.qty_used,
                "qty_returned": line.qty_returned,
                "qty_damaged": line.qty_damaged,
                "unit": line.unit,
                "is_extra": bool(line.is_extra),
            }
            for line in request.lines
        ],
    }


# ---------------------------------------------------------------------------- pembantu


def _transition(request: StockRequest, new_status: str) -> None:
    machines.STOCK_REQUEST.assert_transition(request.status, new_status)
    request.status = new_status
    request.version = (request.version or 1) + 1


def _serialized(db: Session, skus: set[str] | list[str]) -> set[str]:
    if not skus:
        return set()
    rows = db.query(Item.sku).filter(Item.sku.in_(list(skus)), Item.is_serialized.is_(True)).all()
    return {sku for (sku,) in rows}


def _item(db: Session, sku: str) -> Item:
    item = db.get(Item, sku)
    if item is None:
        raise ScmError("UNKNOWN_ITEM", f"Barang {sku} tidak dikenal", 422, {"item_sku": sku})
    return item


def _base_lines(request: StockRequest) -> list[StockRequestLine]:
    return [line for line in request.lines if not line.is_extra]


def _lines_of(request: StockRequest, sku: str) -> list[StockRequestLine]:
    return [line for line in request.lines if line.item_sku == sku]


def _check_low_stock(db: Session, warehouse_code: str, item: Item, before: int, after: int, correlation_id: str) -> None:
    """Saat stok tersedia menyeberang ke bawah ROP, minta PR `LOW_STOCK` (port menjaga satu PR terbuka)."""
    if before >= item.reorder_point > after:
        qty = max(item.reorder_point * 2 - after, 1)
        ports.procurement.request_low_stock_purchase(
            db, item_sku=item.sku, warehouse_code=warehouse_code, qty=qty, correlation_id=correlation_id
        )


def _try_reserve(db: Session, request: StockRequest) -> list[Shortage]:
    """Reservasi semua baris dasar bila semuanya cukup; bila ada yang kurang, tidak ada yang ditahan."""
    lines = _base_lines(request)
    shortages: list[Shortage] = []
    available: dict[str, int] = {}
    for line in lines:
        available[line.item_sku] = ledger.get_available(db, request.warehouse_code, line.item_sku)
        if available[line.item_sku] < line.qty_required:
            shortages.append(Shortage(line.item_sku, line.qty_required - max(available[line.item_sku], 0)))
    if shortages:
        return shortages

    serialized = _serialized(db, [line.item_sku for line in lines])
    for line in lines:
        ledger.reserve(
            db,
            warehouse_code=request.warehouse_code,
            item_sku=line.item_sku,
            qty=line.qty_required,
            ref_type=REF_TYPE,
            ref_no=request.stock_request_no,
            correlation_id=request.ticket_code,
        )
        if line.item_sku in serialized:
            ports.assets.reserve_units(
                db,
                item_sku=line.item_sku,
                warehouse_code=request.warehouse_code,
                qty=line.qty_required,
                stock_request_no=request.stock_request_no,
            )
        item = _item(db, line.item_sku)
        _check_low_stock(
            db, request.warehouse_code, item, available[line.item_sku], available[line.item_sku] - line.qty_required, request.ticket_code
        )
    request.reserved_until = clock.utcnow() + timedelta(hours=RESERVATION_HOURS)
    return []


def _publish_ready(db: Session, request: StockRequest) -> None:
    publish(
        db,
        "stockrequest.ready",
        request.ticket_code,
        {"stock_request_no": request.stock_request_no, "ticket_code": request.ticket_code, "status": "READY_TO_ISSUE"},
    )


# ---------------------------------------------------------------------------- F1, F2


def _validated_ticket(data: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    ticket_code = data.get("ticket_code")
    city_code = (data.get("install_address") or {}).get("city_code")
    items = data.get("required_items")
    if not ticket_code or not city_code or not isinstance(items, list):
        raise ScmError(
            "INVALID_EVENT",
            "ticket.created harus memuat ticket_code, install_address.city_code, dan required_items",
            422,
        )
    for item in items:
        if not item.get("item_sku") or not isinstance(item.get("qty"), int) or item["qty"] <= 0:
            raise ScmError("INVALID_EVENT", "required_items memuat baris yang tidak valid", 422, {"line": item})
    return ticket_code, city_code, items


def create_from_ticket(db: Session, data: dict[str, Any], correlation_id: str | None = None) -> StockRequest | None:
    ticket_code, city_code, items = _validated_ticket(data)
    existing = db.query(StockRequest).filter(StockRequest.ticket_code == ticket_code).first()
    if existing is not None:
        logger.info("ticket.created untuk %s diabaikan: sudah ada %s", ticket_code, existing.stock_request_no)
        return existing
    if not items:
        logger.info("ticket.created untuk %s tanpa required_items: tidak ada permintaan barang", ticket_code)
        return None

    warehouse = db.query(Warehouse).filter(Warehouse.city_code == city_code).first()
    if warehouse is None:
        raise ScmError("UNKNOWN_CITY", f"Tidak ada gudang untuk kota {city_code}", 422, {"city_code": city_code})

    merged: dict[str, dict[str, Any]] = {}
    for item in items:  # satu baris per SKU; jumlah SKU yang sama dijumlahkan
        sku = item["item_sku"]
        master = _item(db, sku)
        entry = merged.setdefault(sku, {"qty": 0, "unit": item.get("unit") or master.unit})
        entry["qty"] += item["qty"]

    request = StockRequest(
        stock_request_no=new_stock_request_no(db),
        ticket_code=ticket_code,
        order_no=data.get("order_no"),
        subscription_code=data.get("subscription_code"),
        city_code=city_code,
        warehouse_code=warehouse.code,
        status="REQUESTED",
    )
    request.lines = [
        StockRequestLine(position=index, item_sku=sku, qty_required=entry["qty"], unit=entry["unit"])
        for index, (sku, entry) in enumerate(merged.items())
    ]
    pending = db.get(PendingAssignment, ticket_code)
    if pending is not None:
        request.technician_employee_id = pending.technician_employee_id
        db.delete(pending)
    db.add(request)
    db.flush()

    correlation = correlation_id or ticket_code
    shortages = _try_reserve(db, request)
    if not shortages:
        _transition(request, "READY_TO_ISSUE")
        _publish_ready(db, request)
        return request

    pr_no = ports.procurement.request_purchase(
        db,
        stock_request_no=request.stock_request_no,
        warehouse_code=request.warehouse_code,
        shortages=shortages,
        correlation_id=correlation,
    )
    request.purchase_request_no = pr_no
    _transition(request, "PENDING_STOCK")
    publish(
        db,
        "stockrequest.pending",
        request.ticket_code,
        {
            "stock_request_no": request.stock_request_no,
            "ticket_code": request.ticket_code,
            "status": "PENDING_STOCK",
            "missing_items": [{"item_sku": s.item_sku, "qty_short": s.qty} for s in shortages],
            "purchase_request_no": pr_no,
        },
    )
    return request


def apply_assignment(db: Session, data: dict[str, Any]) -> None:
    ticket_code = data.get("ticket_code")
    technician = data.get("technician_employee_id")
    if not ticket_code or not technician:
        raise ScmError("INVALID_EVENT", "ticket.assigned harus memuat ticket_code dan technician_employee_id", 422)

    request = db.query(StockRequest).filter(StockRequest.ticket_code == ticket_code).first()
    if request is None:  # event tiba sebelum ticket.created diproses
        pending = db.get(PendingAssignment, ticket_code)
        if pending is None:
            db.add(PendingAssignment(ticket_code=ticket_code, technician_employee_id=technician))
        else:
            pending.technician_employee_id = technician
        return
    if request.status in ("REQUESTED", "PENDING_STOCK", "READY_TO_ISSUE"):
        request.technician_employee_id = technician
    else:
        logger.warning("ticket.assigned untuk %s diabaikan: permintaan sudah %s", ticket_code, request.status)


# ---------------------------------------------------------------------------- F3 pengeluaran


@dataclass
class IssueLine:
    item_sku: str
    qty: int
    serial_numbers: list[str] | None = None


def _stock_issued_event(db: Session, request: StockRequest, actor: Actor, lines: list[dict[str, Any]]) -> None:
    publish(
        db,
        "stock.issued",
        request.ticket_code,
        {
            "stock_request_no": request.stock_request_no,
            "ticket_code": request.ticket_code,
            "technician_employee_id": request.technician_employee_id,
            "issued_by": actor.sub,
            "lines": lines,
            "issued_at": clock.to_wib_iso(clock.utcnow()),
        },
    )


def issue(db: Session, stock_request_no: str, requested: list[IssueLine], actor: Actor) -> dict[str, Any]:
    request = get_by_no(db, stock_request_no, for_update=True)
    machines.STOCK_REQUEST.assert_transition(request.status, "ISSUED")
    if not request.technician_employee_id:
        raise ScmError("TECHNICIAN_NOT_ASSIGNED", "Teknisi belum ditugaskan pada tiket ini", 409, {"ticket_code": request.ticket_code})

    base = _base_lines(request)
    provided: dict[str, IssueLine] = {}
    for line in requested:
        if line.item_sku in provided:
            raise ScmError("ISSUE_LINES_MISMATCH", f"Barang {line.item_sku} muncul lebih dari sekali", 422)
        provided[line.item_sku] = line
    expected = {line.item_sku: line.qty_required for line in base}
    if {sku: line.qty for sku, line in provided.items()} != expected:
        raise ScmError(
            "ISSUE_LINES_MISMATCH",
            "Baris pengeluaran harus sama dengan paket barang permintaan",
            422,
            {"expected": expected, "provided": {sku: line.qty for sku, line in provided.items()}},
        )

    serialized = _serialized(db, list(expected))
    reserved_units = ports.assets.units_for_request(db, stock_request_no=stock_request_no) if serialized else []
    event_lines: list[dict[str, Any]] = []
    for line in base:
        ledger.issue(
            db,
            warehouse_code=request.warehouse_code,
            item_sku=line.item_sku,
            qty=line.qty_required,
            ref_type=REF_TYPE,
            ref_no=request.stock_request_no,
            correlation_id=request.ticket_code,
            actor=actor,
        )
        entry: dict[str, Any] = {"item_sku": line.item_sku, "qty": line.qty_required, "unit": line.unit}
        if line.item_sku in serialized:
            serials = provided[line.item_sku].serial_numbers
            if serials is None:
                if len(serialized) > 1:
                    raise ScmError("SERIAL_NOT_RESERVED", "serial_numbers wajib diisi bila ada lebih dari satu barang serial", 422)
                serials = list(reserved_units)
            if len(serials) != line.qty_required or len(set(serials)) != len(serials) or not set(serials) <= set(reserved_units):
                raise ScmError(
                    "SERIAL_NOT_RESERVED",
                    "Nomor seri harus persis unit yang direservasi untuk permintaan ini",
                    409,
                    {"item_sku": line.item_sku, "provided": serials, "reserved": reserved_units},
                )
            ports.assets.mark_with_technician(
                db,
                stock_request_no=stock_request_no,
                serial_numbers=list(serials),
                technician_employee_id=request.technician_employee_id,
            )
            entry["serial_numbers"] = list(serials)
        line.qty_issued = line.qty_required
        event_lines.append(entry)

    _transition(request, "ISSUED")
    request.reserved_until = None
    _stock_issued_event(db, request, actor, event_lines)
    audit.record(db, actor, "stock_request.issue", "StockRequest", stock_request_no, {"lines": event_lines}, request.ticket_code)
    return {
        "stock_request_no": stock_request_no,
        "status": "ISSUED",
        "unit_status": "WITH_TECHNICIAN" if serialized else "NONE",
    }


def issue_extra(db: Session, stock_request_no: str, lines: list[tuple[str, int]], actor: Actor) -> dict[str, Any]:
    request = get_by_no(db, stock_request_no, for_update=True)
    if request.status != "ISSUED":
        raise ScmError(
            "INVALID_TRANSITION",
            f"STOCK_REQUEST: barang tambahan hanya untuk permintaan ISSUED, status sekarang {request.status}",
            409,
            {"machine": "STOCK_REQUEST", "current": request.status, "requested": "ISSUE_EXTRA", "allowed": ["ISSUED"]},
        )
    skus = [sku for sku, _ in lines]
    serialized = _serialized(db, skus)
    position = max((line.position for line in request.lines), default=-1)
    event_lines: list[dict[str, Any]] = []
    for sku, qty in lines:
        item = _item(db, sku)
        before = ledger.get_available(db, request.warehouse_code, sku)
        ledger.issue_extra(
            db,
            warehouse_code=request.warehouse_code,
            item_sku=sku,
            qty=qty,
            ref_type=REF_TYPE,
            ref_no=request.stock_request_no,
            correlation_id=request.ticket_code,
            actor=actor,
        )
        entry: dict[str, Any] = {"item_sku": sku, "qty": qty, "unit": item.unit}
        if sku in serialized:
            units = ports.assets.reserve_units(
                db, item_sku=sku, warehouse_code=request.warehouse_code, qty=qty, stock_request_no=stock_request_no
            )
            ports.assets.mark_with_technician(
                db,
                stock_request_no=stock_request_no,
                serial_numbers=list(units),
                technician_employee_id=request.technician_employee_id,
            )
            entry["serial_numbers"] = list(units)
        position += 1
        request.lines.append(
            StockRequestLine(position=position, item_sku=sku, qty_required=qty, qty_issued=qty, unit=item.unit, is_extra=True)
        )
        event_lines.append(entry)
        _check_low_stock(db, request.warehouse_code, item, before, before - qty, request.ticket_code)

    _stock_issued_event(db, request, actor, event_lines)
    audit.record(db, actor, "stock_request.issue_extra", "StockRequest", stock_request_no, {"lines": event_lines}, request.ticket_code)
    return {"stock_request_no": stock_request_no, "status": request.status, "lines_added": len(event_lines)}


# ---------------------------------------------------------------------------- F4 laporan pemakaian


def report_items(db: Session, data: dict[str, Any]) -> StockRequest | None:
    stock_request_no = data.get("stock_request_no")
    ticket_code = data.get("ticket_code")
    reported = data.get("lines")
    if not stock_request_no or not isinstance(reported, list):
        raise ScmError("INVALID_EVENT", "ticket.items_reported harus memuat stock_request_no dan lines", 422)

    request = get_by_no(db, stock_request_no, for_update=True)
    if ticket_code and ticket_code != request.ticket_code:
        raise ScmError(
            "TICKET_MISMATCH",
            f"Tiket {ticket_code} bukan milik {stock_request_no}",
            422,
            {"expected": request.ticket_code, "provided": ticket_code},
        )
    if request.status != "ISSUED":
        logger.warning("ticket.items_reported untuk %s diabaikan: status %s", stock_request_no, request.status)
        return None

    issued_skus = {line.item_sku for line in request.lines}
    reports: dict[str, dict[str, Any]] = {}
    for line in reported:
        sku = line.get("item_sku")
        if sku not in issued_skus:
            raise ScmError("ITEM_NOT_ISSUED", f"Barang {sku} tidak dikeluarkan pada permintaan ini", 422, {"item_sku": sku})
        entry = reports.setdefault(sku, {"used": 0, "returned": 0, "installed": []})
        entry["used"] += int(line.get("used", 0))
        entry["returned"] += int(line.get("returned", 0))
        entry["installed"] += list(line.get("serial_numbers_installed") or [])

    serialized = _serialized(db, issued_skus)
    issued_serials = ports.assets.units_for_request(db, stock_request_no=stock_request_no) if serialized else []
    installed_all: list[str] = []
    has_discrepancy = False
    result_lines: list[dict[str, Any]] = []

    for sku in sorted(issued_skus, key=lambda s: min(line.position for line in _lines_of(request, s))):
        lines = _lines_of(request, sku)
        issued = sum(line.qty_issued for line in lines)
        report = reports.get(sku, {"used": 0, "returned": 0, "installed": []})
        used = min(report["used"], issued)
        returned = max(min(report["returned"], issued - used), 0)
        if report["used"] + report["returned"] != issued:
            has_discrepancy = True
        if sku in serialized and len(report["installed"]) != report["used"]:
            has_discrepancy = True
        flagged = sum(line.qty_damaged for line in lines)
        damaged = min(flagged, returned)

        remaining_used, remaining_returned = used, returned
        for line in lines:
            line.qty_used = min(remaining_used, line.qty_issued)
            remaining_used -= line.qty_used
        for line in lines:
            line.qty_returned = min(remaining_returned, line.qty_issued - line.qty_used)
            remaining_returned -= line.qty_returned

        if sku in serialized:
            installed_all += report["installed"]
            good = 0  # unit serial masuk saldo setelah diperiksa (Slice C), kecuali yang rusak
        else:
            good = returned - damaged
        if good > 0:
            ledger.return_good(
                db, warehouse_code=request.warehouse_code, item_sku=sku, qty=good,
                ref_type=REF_TYPE, ref_no=stock_request_no, correlation_id=request.ticket_code,
            )
        if damaged > 0:
            ledger.return_damaged(
                db, warehouse_code=request.warehouse_code, item_sku=sku, qty=damaged,
                ref_type=REF_TYPE, ref_no=stock_request_no, correlation_id=request.ticket_code,
            )
        result_lines.append({"item_sku": sku, "issued": issued, "used": used, "returned": returned, "damaged": damaged})

    if installed_all:
        ports.assets.mark_installed(db, serial_numbers=installed_all, ticket_code=request.ticket_code)
    returned_serials = [serial for serial in issued_serials if serial not in set(installed_all)]
    if returned_serials:
        ports.assets.mark_returned(db, serial_numbers=returned_serials)

    request.discrepancy = has_discrepancy
    _transition(request, "RETURNED")
    publish(
        db,
        "stock.returned",
        request.ticket_code,
        {
            "stock_request_no": stock_request_no,
            "ticket_code": request.ticket_code,
            "status": "RETURNED",
            "lines": result_lines,
            "has_discrepancy": has_discrepancy,
            "returned_at": clock.to_wib_iso(clock.utcnow()),
        },
    )
    audit.record(
        db, data.get("reported_by") or SYSTEM_ACTOR, "stock_request.items_reported", "StockRequest", stock_request_no,
        {"lines": result_lines, "has_discrepancy": has_discrepancy}, request.ticket_code,
    )
    return request


# ---------------------------------------------------------------------------- F5 barang rusak


def flag_damaged(
    db: Session,
    stock_request_no: str,
    item_sku: str,
    qty: int,
    serial_number: str | None,
    notes: str | None,
    actor: Actor,
) -> dict[str, Any]:
    request = get_by_no(db, stock_request_no, for_update=True)
    if request.status not in ("ISSUED", "RETURNED"):
        raise ScmError(
            "INVALID_TRANSITION",
            f"STOCK_REQUEST: tandai rusak hanya untuk ISSUED atau RETURNED, status sekarang {request.status}",
            409,
            {"machine": "STOCK_REQUEST", "current": request.status, "requested": "FLAG_DAMAGED", "allowed": ["ISSUED", "RETURNED"]},
        )
    lines = _lines_of(request, item_sku)
    if not lines:
        raise ScmError("ITEM_NOT_ISSUED", f"Barang {item_sku} tidak ada pada permintaan ini", 422, {"item_sku": item_sku})

    serial = bool(_serialized(db, [item_sku]))
    if serial:
        if request.status == "RETURNED":
            raise ScmError(
                "USE_UNIT_INSPECTION",
                "Unit serial yang sudah kembali dinilai lewat pemeriksaan unit retur, bukan tandai rusak",
                409,
                {"item_sku": item_sku},
            )
        if not serial_number or qty != 1:
            raise ScmError("SERIAL_NUMBER_REQUIRED", "Barang serial ditandai rusak satu unit per permintaan dengan serial_number", 422)
        if serial_number not in ports.assets.units_for_request(db, stock_request_no=stock_request_no):
            raise ScmError(
                "SERIAL_NOT_IN_REQUEST", f"Nomor seri {serial_number} bukan bagian dari {stock_request_no}", 409,
                {"serial_number": serial_number},
            )

    issued = sum(line.qty_issued for line in lines)
    returned = sum(line.qty_returned for line in lines)
    already = sum(line.qty_damaged for line in lines)
    limit = issued if request.status == "ISSUED" else returned
    if already + qty > limit:
        raise ScmError(
            "DAMAGED_EXCEEDS_LIMIT",
            f"Jumlah rusak {item_sku} melebihi batas",
            409,
            {"item_sku": item_sku, "already_damaged": already, "requested": qty, "limit": limit},
        )

    if serial:
        ports.assets.mark_faulty(db, serial_number=serial_number, notes=notes)
    elif request.status == "RETURNED":
        item = _item(db, item_sku)
        before = ledger.get_available(db, request.warehouse_code, item_sku)
        ledger.mark_damaged(
            db, warehouse_code=request.warehouse_code, item_sku=item_sku, qty=qty,
            ref_type=REF_TYPE, ref_no=stock_request_no, correlation_id=request.ticket_code, actor=actor,
        )
        _check_low_stock(db, request.warehouse_code, item, before, before - qty, request.ticket_code)
    lines[0].qty_damaged += qty
    audit.record(
        db, actor, "stock_request.flag_damaged", "StockRequest", stock_request_no,
        {"item_sku": item_sku, "qty": qty, "serial_number": serial_number, "notes": notes}, request.ticket_code,
    )
    return {"stock_request_no": stock_request_no, "item_sku": item_sku, "qty_damaged": already + qty}


# ---------------------------------------------------------------------------- F7 batal dan kedaluwarsa


def _release_and_cancel(db: Session, request: StockRequest, reason: str, actor: Actor | str) -> None:
    was_ready = request.status == "READY_TO_ISSUE"
    machines.STOCK_REQUEST.assert_transition(request.status, "CANCELLED")
    if was_ready:
        base = _base_lines(request)
        for line in base:
            ledger.release(
                db, warehouse_code=request.warehouse_code, item_sku=line.item_sku, qty=line.qty_required,
                ref_type=REF_TYPE, ref_no=request.stock_request_no, correlation_id=request.ticket_code,
                actor=actor,
            )
        if _serialized(db, [line.item_sku for line in base]):
            ports.assets.release_units(db, stock_request_no=request.stock_request_no)
    _transition(request, "CANCELLED")
    request.cancel_reason = reason
    request.reserved_until = None
    audit.record(
        db, actor, "stock_request.cancel", "StockRequest", request.stock_request_no, {"reason": reason}, request.ticket_code
    )
    if was_ready:  # stok yang dilepas bisa memenuhi permintaan lain yang menunggu
        for line in _base_lines(request):
            reevaluate_pending(db, item_sku=line.item_sku, warehouse_code=request.warehouse_code)


def cancel(db: Session, stock_request_no: str, reason: str, actor: Actor) -> dict[str, Any]:
    request = get_by_no(db, stock_request_no, for_update=True)
    _release_and_cancel(db, request, reason, actor)
    return {"stock_request_no": stock_request_no, "status": request.status}


def expire_due(db: Session) -> list[str]:
    """Batalkan permintaan `READY_TO_ISSUE` yang reservasinya lewat 72 jam; kembalikan nomornya."""
    now = clock.utcnow()
    due = (
        db.query(StockRequest)
        .filter(StockRequest.status == "READY_TO_ISSUE", StockRequest.reserved_until.isnot(None), StockRequest.reserved_until <= now)
        .order_by(StockRequest.reserved_until)
        .with_for_update()
        .all()
    )
    expired: list[str] = []
    for request in due:
        if request.status != "READY_TO_ISSUE":  # diubah oleh pelepasan berantai di iterasi sebelumnya
            continue
        _release_and_cancel(db, request, "RESERVATION_EXPIRED", SYSTEM_ACTOR)
        expired.append(request.stock_request_no)
    return expired


# ---------------------------------------------------------------------------- F8 langkah akhir: barang masuk


def reevaluate_pending(db: Session, *, item_sku: str, warehouse_code: str) -> list[str]:
    """Permintaan `PENDING_STOCK` yang memuat SKU itu dicoba lagi urut tertua; yang kini cukup menjadi siap."""
    candidates = (
        db.query(StockRequest)
        .join(StockRequestLine, StockRequestLine.stock_request_id == StockRequest.id)
        .filter(
            StockRequest.status == "PENDING_STOCK",
            StockRequest.warehouse_code == warehouse_code,
            StockRequestLine.item_sku == item_sku,
            StockRequestLine.is_extra.is_(False),
        )
        .order_by(StockRequest.created_at, StockRequest.stock_request_no)
        .with_for_update()
        .all()
    )
    ready: list[str] = []
    for request in candidates:
        if _try_reserve(db, request):
            continue
        _transition(request, "READY_TO_ISSUE")
        _publish_ready(db, request)
        ready.append(request.stock_request_no)
    return ready


class StockRequestService:
    """Implementasi `StockRequestPort` (dipanggil Slice B setelah penerimaan barang)."""

    def reevaluate_pending(self, db: Session, *, item_sku: str, warehouse_code: str) -> list[str]:
        return reevaluate_pending(db, item_sku=item_sku, warehouse_code=warehouse_code)

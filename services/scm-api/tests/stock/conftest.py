"""Fixture Slice A: port palsu (aset dan pengadaan), pembuat event tiket, dan pembaca hasil."""
import itertools
import json
from datetime import timedelta

import pytest
from sqlalchemy import text

from app.core import clock
from app.core.errors import ScmError
from app.core.models import OutboxEvent
from app.core.ports import override
from app.stock.models import StockRequest


class FakeAssets:
    """Meniru `AssetPort`: unit `IN_STOCK` per (sku, gudang) dipilih FIFO, status dilacak di memori."""

    def __init__(self) -> None:
        self.pool: dict[tuple[str, str], list[str]] = {}
        self.status: dict[str, str] = {}
        self.by_request: dict[str, list[str]] = {}
        self.counter = itertools.count(1)
        self.calls: list[tuple[str, dict]] = []
        self.origin: dict[str, tuple[str, str]] = {}

    def stock(self, sku: str, warehouse: str, qty: int) -> list[str]:
        serials = [f"SN-FAKE-{next(self.counter):04d}" for _ in range(qty)]
        self.pool.setdefault((sku, warehouse), []).extend(serials)
        for serial in serials:
            self.status[serial] = "IN_STOCK"
            self.origin[serial] = (sku, warehouse)
        return serials

    def register_units(self, db, *, item_sku, warehouse_code, qty, gr_no):
        self.calls.append(("register_units", {"qty": qty}))
        return self.stock(item_sku, warehouse_code, qty)

    def reserve_units(self, db, *, item_sku, warehouse_code, qty, stock_request_no):
        self.calls.append(("reserve_units", {"sku": item_sku, "qty": qty, "request": stock_request_no}))
        pool = self.pool.setdefault((item_sku, warehouse_code), [])
        if len(pool) < qty:
            raise ScmError("INSUFFICIENT_STOCK", "unit kurang", 409)
        taken, self.pool[(item_sku, warehouse_code)] = pool[:qty], pool[qty:]
        for serial in taken:
            self.status[serial] = "RESERVED"
        self.by_request.setdefault(stock_request_no, []).extend(taken)
        return taken

    def release_units(self, db, *, stock_request_no):
        self.calls.append(("release_units", {"request": stock_request_no}))
        for serial in self.by_request.pop(stock_request_no, []):
            if self.status[serial] == "RESERVED":
                self.status[serial] = "IN_STOCK"
                self.pool.setdefault(self.origin[serial], []).insert(0, serial)

    def units_for_request(self, db, *, stock_request_no):
        return list(self.by_request.get(stock_request_no, []))

    def mark_with_technician(self, db, *, stock_request_no, serial_numbers, technician_employee_id):
        self.calls.append(("mark_with_technician", {"serials": list(serial_numbers), "tech": technician_employee_id}))
        for serial in serial_numbers:
            if serial not in self.by_request.get(stock_request_no, []) or self.status[serial] != "RESERVED":
                raise ScmError("SERIAL_NOT_RESERVED", "bukan unit reservasi", 409)
        for serial in serial_numbers:
            self.status[serial] = "WITH_TECHNICIAN"
        return list(serial_numbers)

    def mark_installed(self, db, *, serial_numbers, ticket_code):
        self.calls.append(("mark_installed", {"serials": list(serial_numbers), "ticket": ticket_code}))
        for serial in serial_numbers:
            self.status[serial] = "INSTALLED"

    def mark_returned(self, db, *, serial_numbers):
        self.calls.append(("mark_returned", {"serials": list(serial_numbers)}))
        for serial in serial_numbers:
            if self.status[serial] != "FAULTY":
                self.status[serial] = "RETURNED"

    def mark_faulty(self, db, *, serial_number, notes=None):
        self.calls.append(("mark_faulty", {"serial": serial_number}))
        self.status[serial_number] = "FAULTY"


class FakeProcurement:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.low_stock: list[dict] = []

    def request_purchase(self, db, *, stock_request_no, warehouse_code, shortages, correlation_id):
        self.requests.append(
            {"stock_request_no": stock_request_no, "warehouse_code": warehouse_code, "shortages": list(shortages), "correlation_id": correlation_id}
        )
        return f"PR-FAKE-{len(self.requests):04d}"

    def request_low_stock_purchase(self, db, *, item_sku, warehouse_code, qty, correlation_id):
        self.low_stock.append({"item_sku": item_sku, "warehouse_code": warehouse_code, "qty": qty})
        return f"PR-LOW-{len(self.low_stock):04d}"


@pytest.fixture
def assets():
    fake = FakeAssets()
    fake.stock("ONT-01", "WH-BDG", 20)
    fake.stock("ONT-01", "WH-SBY", 15)
    return fake


@pytest.fixture
def procurement():
    return FakeProcurement()


@pytest.fixture(autouse=True)
def fake_ports(assets, procurement):
    with override(procurement=procurement, assets=assets):
        yield


def ticket_data(ticket_code="TKT-000001", city="BDG", items=None):
    items = items if items is not None else [("ONT-01", 1, "UNIT"), ("CBL-FO", 50, "METER")]
    return {
        "ticket_code": ticket_code,
        "type": "INSTALLATION",
        "order_no": "ORD-2026-000125",
        "subscription_code": "SUB-000012",
        "customer_code": "CUS-000456",
        "install_address": {"address_code": "ADR-000010", "address": "Jl. Dago No. 12", "city_code": city, "postal_code": "40135"},
        "recipient": {"name": "Andi", "whatsapp": "6281234567890", "email": "andi@gmail.com"},
        "required_items": [{"item_sku": sku, "qty": qty, "unit": unit} for sku, qty, unit in items],
    }


@pytest.fixture
def make_ticket():
    return ticket_data


@pytest.fixture
def send(client, signed_event):
    """Kirim event bertanda tangan ke `/internal/events`; kembalikan respons."""

    def _send(event_type: str, data: dict, event_id: str | None = None, correlation_id: str | None = None):
        raw, headers, _ = signed_event(event_type, data, correlation_id or data.get("ticket_code", "TKT-000001"), event_id)
        return client.post("/internal/events", content=raw, headers=headers)

    return _send


@pytest.fixture
def create_request(send, seeded_db):
    def _create(ticket_code="TKT-000001", city="BDG", items=None, technician="EMP-0042") -> str:
        response = send("ticket.created", ticket_data(ticket_code, city, items))
        assert response.status_code == 200, response.text
        if technician:
            assigned = send(
                "ticket.assigned",
                {"ticket_code": ticket_code, "subscription_code": "SUB-000012", "technician_employee_id": technician,
                 "assigned_by": "EMP-0010", "city_code": city, "assigned_at": "2026-11-25T10:00:00+07:00"},
            )
            assert assigned.status_code == 200, assigned.text
        seeded_db.expire_all()
        return seeded_db.query(StockRequest).filter_by(ticket_code=ticket_code).one().stock_request_no

    return _create


@pytest.fixture
def events_of(seeded_db):
    """Daftar `(event_type, data)` di outbox, urut dibuat."""

    def _events(event_type: str | None = None) -> list[tuple[str, dict]]:
        seeded_db.expire_all()
        # SQLite menyimpan baris berurutan menurut rowid; `created_at` hanya beresolusi detik dan `id` berupa UUID acak.
        rows = seeded_db.query(OutboxEvent).order_by(text("rowid")).all()
        return [(r.event_type, json.loads(r.payload_json)) for r in rows if event_type in (None, r.event_type)]

    return _events


@pytest.fixture
def frozen_clock(monkeypatch):
    """Jam yang bisa dimajukan: `frozen_clock.advance(hours=73)`."""

    class Clock:
        now = clock.utcnow()

        def advance(self, **kwargs):
            self.now = self.now + timedelta(**kwargs)

    state = Clock()
    monkeypatch.setattr(clock, "utcnow", lambda: state.now)
    return state

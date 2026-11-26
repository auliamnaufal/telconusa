import json

from app.core import audit, codes
from app.core.auth import Actor
from app.core.models import AuditLog, OutboxEvent
from app.core.outbox import publish


def test_publish_adds_pending_scm_event(db):
    event_id = publish(db, "stock.issued", "TKT-000001", {"stock_request_no": "SR-2026-000001"})
    db.commit()

    row = db.query(OutboxEvent).one()
    assert row.event_id == event_id
    assert row.status == "PENDING"
    assert row.source == "scm"
    assert row.correlation_id == "TKT-000001"
    assert json.loads(row.payload_json) == {"stock_request_no": "SR-2026-000001"}


def test_published_event_disappears_with_rolled_back_transaction(db):
    publish(db, "stock.issued", "TKT-000001", {})
    db.rollback()
    assert db.query(OutboxEvent).count() == 0


def test_audit_record_stores_actor_role_and_detail(db):
    audit.record(db, Actor(sub="EMP-0020", role="SCM_MANAGER"), "stock_request.cancel", "StockRequest", "SR-2026-000001", {"reason": "batal"}, "TKT-000001")
    db.commit()

    row = db.query(AuditLog).one()
    assert (row.actor, row.role, row.action) == ("EMP-0020", "SCM_MANAGER", "stock_request.cancel")
    assert json.loads(row.detail) == {"reason": "batal"}
    assert row.correlation_id == "TKT-000001"


def test_business_codes_are_sequential_and_formatted(db):
    year = codes.clock.current_year()
    assert [codes.new_stock_request_no(db) for _ in range(2)] == [f"SR-{year}-000001", f"SR-{year}-000002"]
    assert codes.new_purchase_request_no(db) == f"PR-{year}-0001"
    assert codes.new_purchase_order_no(db) == f"PO-{year}-0001"
    assert codes.new_goods_receipt_no(db) == f"GR-{year}-0001"
    assert codes.new_serial_number(db) == f"SN-ONT-{year}-000001"
    assert codes.new_vendor_code(db) == "VEN-0001"
    assert codes.new_stock_request_no(db) == f"SR-{year}-000003"

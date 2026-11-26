import pytest
from fastapi import HTTPException

from app.core import machines


def assert_blocked(machine, current: str, new: str) -> HTTPException:
    with pytest.raises(HTTPException) as exc:
        machine.assert_transition(current, new)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "INVALID_TRANSITION"
    return exc.value


def test_purchase_request_happy_path_and_retry_after_rejection():
    pr = machines.PURCHASE_REQUEST
    pr.assert_transition("PENDING_BUDGET", "BUDGET_OK")
    pr.assert_transition("BUDGET_OK", "PO_CREATED")
    pr.assert_transition("BUDGET_REJECTED", "PENDING_BUDGET")


def test_purchase_request_cannot_skip_budget_check():
    assert_blocked(machines.PURCHASE_REQUEST, "PENDING_BUDGET", "PO_CREATED")
    assert_blocked(machines.PURCHASE_REQUEST, "PO_CREATED", "CANCELLED")


def test_purchase_order_is_never_born_approved_and_follows_the_chain():
    po = machines.PURCHASE_ORDER
    for current, new in [
        ("DRAFT", "PENDING_APPROVAL"),
        ("PENDING_APPROVAL", "APPROVED"),
        ("APPROVED", "PARTIALLY_RECEIVED"),
        ("PARTIALLY_RECEIVED", "RECEIVED"),
        ("RECEIVED", "CLOSED"),
    ]:
        po.assert_transition(current, new)
    assert_blocked(po, "DRAFT", "APPROVED")


def test_rejected_or_received_orders_cannot_be_approved_or_cancelled_again():
    po = machines.PURCHASE_ORDER
    assert_blocked(po, "REJECTED", "APPROVED")
    assert_blocked(po, "PARTIALLY_RECEIVED", "CANCELLED")
    err = assert_blocked(po, "PENDING_APPROVAL", "RECEIVED")
    assert "APPROVED" in err.detail["details"]["allowed"]


def test_stock_request_and_unit_machines_come_from_shared():
    machines.STOCK_REQUEST.assert_transition("READY_TO_ISSUE", "ISSUED")
    machines.UNIT.assert_transition("RESERVED", "WITH_TECHNICIAN")
    assert_blocked(machines.UNIT, "IN_STOCK", "WITH_TECHNICIAN")


def test_goods_receipt_is_immutable_once_posted():
    assert_blocked(machines.GOODS_RECEIPT, "POSTED", "CANCELLED")

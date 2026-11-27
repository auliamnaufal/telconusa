import pytest

from app.core.models import AuditLog

# Harga ONT Rp350.000: 14 unit = Rp4,9 juta; 100 = Rp35 juta; 429 = Rp150,15 juta.
SMALL, MEDIUM, LARGE = 14, 100, 429


def _error(response):
    return response.status_code, response.json()["error"]["code"]


@pytest.mark.parametrize(
    "qty,roles",
    [
        (SMALL, ["SCM_MANAGER"]),
        (MEDIUM, ["FINANCE_MANAGER", "SCM_MANAGER"]),
        (LARGE, ["DIRECTOR", "FINANCE_MANAGER", "SCM_MANAGER"]),
    ],
)
def test_po_is_approved_only_after_every_required_role(create_po, decide, seeded_db, qty, roles):
    po_no = create_po(qty)
    for index, role in enumerate(roles):
        response = decide(po_no, role)
        assert response.status_code == 200, response.text
        expected = "APPROVED" if index == len(roles) - 1 else "PENDING_APPROVAL"
        assert response.json()["status"] == expected
        assert len(response.json()["approvals"]) == index + 1
    assert seeded_db.query(AuditLog).filter_by(entity_id=po_no, action="purchase_order.approve").count() == len(roles)


def test_creator_cannot_approve_own_po(create_po, decide):
    po_no = create_po(SMALL, creator="EMP-0020")
    assert _error(decide(po_no, "SCM_MANAGER", sub="EMP-0020")) == (403, "APPROVAL_SELF_FORBIDDEN")


def test_role_approves_once(create_po, decide):
    po_no = create_po(MEDIUM)
    decide(po_no, "SCM_MANAGER")
    assert _error(decide(po_no, "SCM_MANAGER")) == (409, "DUPLICATE_APPROVAL")


def test_role_outside_the_chain(create_po, decide):
    po_no = create_po(SMALL)
    assert _error(decide(po_no, "DIRECTOR")) == (403, "APPROVAL_ROLE_NOT_REQUIRED")


def test_one_rejection_closes_the_po(create_po, decide):
    po_no = create_po(MEDIUM)
    assert decide(po_no, "FINANCE_MANAGER", "reject").json()["status"] == "REJECTED"
    assert _error(decide(po_no, "SCM_MANAGER")) == (409, "INVALID_TRANSITION")


def test_staff_cannot_approve(client, auth, create_po):
    po_no = create_po(SMALL)
    response = client.post(f"/api/v1/purchase-orders/{po_no}/approve", json={}, headers=auth("PROCUREMENT_STAFF", "EMP-0022"))
    assert response.status_code == 403


def test_finance_manager_can_read_orders(client, auth, create_po):
    po_no = create_po(MEDIUM)
    assert client.get("/api/v1/purchase-orders", headers=auth("FINANCE_MANAGER")).json()[0]["po_no"] == po_no
    assert client.get(f"/api/v1/purchase-orders/{po_no}", headers=auth("FINANCE_MANAGER")).status_code == 200

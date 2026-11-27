import pytest

URL = "/api/v1/purchase-orders"
# Kabel Rp4.000 per meter.
EXACTLY_50M, ABOVE_50M = 12_500, 15_000


@pytest.fixture
def staff(auth, seeded_db):
    return auth("PROCUREMENT_STAFF", "EMP-0021")


@pytest.fixture
def new_po(client, staff):
    def _new(qty=ABOVE_50M):
        response = client.post(URL, json={"vendor_code": "VEN-0001", "item_sku": "CBL-FO", "qty": qty}, headers=staff)
        assert response.status_code == 201, response.text
        return response.json()

    return _new


@pytest.fixture
def quote(client, staff):
    def _quote(po_no, vendor, headers=None):
        return client.post(
            f"{URL}/{po_no}/quotes",
            json={"vendor_code": vendor, "unit_price": 3_900, "notes": "franko gudang"},
            headers=headers or staff,
        )

    return _quote


def _error(response):
    return response.status_code, response.json()["error"]["code"]


def test_po_of_exactly_50_million_needs_no_quotes(new_po):
    assert new_po(EXACTLY_50M)["status"] == "PENDING_APPROVAL"


def test_large_po_is_submitted_only_with_three_quotes(client, staff, new_po, quote):
    created = new_po()
    assert created["status"] == "DRAFT"
    po_no = created["po_no"]
    quote(po_no, "VEN-0001")
    quote(po_no, "VEN-0002")
    assert _error(client.post(f"{URL}/{po_no}/submit", headers=staff)) == (409, "QUOTES_REQUIRED")

    third = quote(po_no, "VEN-0003")
    assert third.status_code == 201
    assert len(third.json()["quotes"]) == 3
    submitted = client.post(f"{URL}/{po_no}/submit", headers=staff)
    assert submitted.json()["status"] == "PENDING_APPROVAL"


def test_same_vendor_twice_is_rejected(new_po, quote):
    po_no = new_po()["po_no"]
    quote(po_no, "VEN-0001")
    assert _error(quote(po_no, "VEN-0001")) == (409, "DUPLICATE_QUOTE")


def test_unknown_vendor(new_po, quote):
    assert _error(quote(new_po()["po_no"], "VEN-9999")) == (404, "VENDOR_NOT_FOUND")


def test_draft_po_cannot_be_approved(new_po, decide):
    assert _error(decide(new_po()["po_no"], "SCM_MANAGER")) == (409, "INVALID_TRANSITION")


def test_quotes_and_submit_only_on_draft(client, staff, new_po, quote):
    po_no = new_po(EXACTLY_50M)["po_no"]
    assert _error(quote(po_no, "VEN-0002")) == (409, "INVALID_TRANSITION")
    assert _error(client.post(f"{URL}/{po_no}/submit", headers=staff)) == (409, "INVALID_TRANSITION")


def test_warehouse_staff_cannot_add_quotes(auth, new_po, quote):
    response = quote(new_po()["po_no"], "VEN-0002", headers=auth("WAREHOUSE_STAFF"))
    assert response.status_code == 403

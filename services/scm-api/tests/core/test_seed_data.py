from app.assets.models import SerializedUnit
from app.catalog.models import PackageKit
from app.core.models import InventoryBalance, Item, StockMovement, Vendor, Warehouse
from app.seed import seed_all

LIVE_UNIT_STATUSES = ("IN_STOCK", "RESERVED", "FAULTY")


def counts(db) -> dict[str, int]:
    return {
        model.__name__: db.query(model).count()
        for model in (Warehouse, Item, Vendor, InventoryBalance, SerializedUnit, PackageKit)
    }


def test_seed_contains_the_agreed_catalog(seeded_db):
    db = seeded_db
    assert {w.code: w.city_code for w in db.query(Warehouse)} == {"WH-BKS": "JKT", "WH-BDG": "BDG", "WH-SBY": "SBY"}
    assert {i.sku: i.is_serialized for i in db.query(Item)} == {
        "ONT-01": True, "SIM-01": False, "RTR-AX": False, "CBL-FO": False,
    }
    assert db.get(Item, "ONT-01").unit_cost == 350000
    assert db.get(Item, "CBL-FO").unit == "METER"
    assert sorted(v.code for v in db.query(Vendor)) == ["VEN-0001", "VEN-0002", "VEN-0003", "VEN-0004"]
    kit = db.get(PackageKit, "HOME-50")
    assert sorted((line.item_sku, line.qty, line.unit) for line in kit.lines) == [("CBL-FO", 50, "METER"), ("ONT-01", 1, "UNIT")]


def test_serialized_stock_equals_the_number_of_units_in_every_warehouse(seeded_db):
    db = seeded_db
    serialized = [item.sku for item in db.query(Item).filter(Item.is_serialized.is_(True))]
    assert serialized == ["ONT-01"]
    for balance in db.query(InventoryBalance).filter(InventoryBalance.item_sku.in_(serialized)):
        units = db.query(SerializedUnit).filter(
            SerializedUnit.item_sku == balance.item_sku, SerializedUnit.warehouse_code == balance.warehouse_code
        )
        live = units.filter(SerializedUnit.status.in_(LIVE_UNIT_STATUSES)).count()
        faulty = units.filter(SerializedUnit.status == "FAULTY").count()
        assert balance.qty_physical == live, balance.warehouse_code
        assert balance.qty_damaged == faulty, balance.warehouse_code


def test_seed_is_idempotent(seeded_db):
    db = seeded_db
    before = counts(db)
    seed_all(db)
    db.commit()
    assert counts(db) == before


def test_seed_serial_numbers_are_unique_and_follow_the_business_format(seeded_db):
    serials = [u.serial_number for u in seeded_db.query(SerializedUnit).order_by(SerializedUnit.received_at)]
    assert len(serials) == len(set(serials)) == 75
    assert serials[0].startswith("SN-ONT-") and serials[0].endswith("-000001")


def test_seed_balances_have_no_negative_or_oversold_stock(seeded_db):
    for balance in seeded_db.query(InventoryBalance):
        assert balance.qty_available >= 0
    assert seeded_db.query(StockMovement).count() == 0

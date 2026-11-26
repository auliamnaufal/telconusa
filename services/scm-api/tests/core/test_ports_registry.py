import pytest

from app.core.ports import Ports, Shortage, override, ports


class FakeAssets:
    def reserve_units(self, db, **kwargs):
        return ["SN-FAKE-1"]


def test_unimplemented_ports_fail_loudly_and_name_the_owning_issue():
    fresh = Ports()  # instans baru: semua port masih stub, tidak bergantung pada slice mana yang sudah selesai
    with pytest.raises(NotImplementedError, match=r"AssetPort\.reserve_units belum diimplementasikan \(SCM-C-01\)"):
        fresh.assets.reserve_units(None, item_sku="ONT-01", warehouse_code="WH-BDG", qty=1, stock_request_no="SR-1")
    with pytest.raises(NotImplementedError, match=r"\(SCM-B-01\)"):
        fresh.procurement.request_purchase(
            None, stock_request_no="SR-1", warehouse_code="WH-BDG", shortages=[Shortage("ONT-01", 1)], correlation_id="TKT-1"
        )
    with pytest.raises(NotImplementedError, match=r"\(SCM-B-01\)"):
        fresh.procurement.request_low_stock_purchase(
            None, item_sku="ONT-01", warehouse_code="WH-BDG", qty=10, correlation_id="TKT-1"
        )
    with pytest.raises(NotImplementedError, match=r"\(SCM-A-09\)"):
        fresh.stock_requests.reevaluate_pending(None, item_sku="ONT-01", warehouse_code="WH-BDG")


def test_override_swaps_one_port_and_restores_everything_afterwards():
    original = (ports.procurement, ports.assets, ports.stock_requests)
    fake = FakeAssets()

    with override(assets=fake):
        assert ports.assets is fake
        assert ports.assets.reserve_units(None) == ["SN-FAKE-1"]
        assert ports.procurement is original[0]

    assert (ports.procurement, ports.assets, ports.stock_requests) == original


def test_override_restores_even_when_the_body_raises():
    original = ports.assets
    with pytest.raises(RuntimeError):
        with override(assets=FakeAssets()):
            raise RuntimeError("boom")
    assert ports.assets is original

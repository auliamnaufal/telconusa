"""Port antar-slice (ADR-0003).

Slice saling memanggil lewat antarmuka tetap supaya tidak ada yang menunggu implementasi slice
lain. Setiap port punya implementasi bawaan (stub) yang gagal keras dengan menyebut issue
pemiliknya; tidak ada stub yang pura-pura berhasil. Slice pemilik mendaftarkan implementasinya di
`app/<slice>/__init__.py` (`ports.assets = AssetService()`), dan tes memakai `ports.override`.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Protocol

from sqlalchemy.orm import Session


@dataclass(frozen=True)
class Shortage:
    item_sku: str
    qty: int


class ProcurementPort(Protocol):
    """Diimplementasikan Slice B (SCM-B-01)."""

    def request_purchase(
        self,
        db: Session,
        *,
        stock_request_no: str,
        warehouse_code: str,
        shortages: list[Shortage],
        correlation_id: str,
    ) -> str:
        """Buat (atau kembalikan) PR untuk permintaan barang itu dan kembalikan `pr_no`."""
        ...


class AssetPort(Protocol):
    """Diimplementasikan Slice C (SCM-C-01). Semua perubahan status unit lewat port ini."""

    def register_units(self, db: Session, *, item_sku: str, warehouse_code: str, qty: int, gr_no: str) -> list[str]:
        """Daftarkan `qty` unit baru `IN_STOCK`; kembalikan nomor serinya."""
        ...

    def reserve_units(
        self, db: Session, *, item_sku: str, warehouse_code: str, qty: int, stock_request_no: str
    ) -> list[str]:
        """Reservasi `qty` unit `IN_STOCK` tertua (FIFO); kurang dari `qty` -> INSUFFICIENT_STOCK."""
        ...

    def release_units(self, db: Session, *, stock_request_no: str) -> None:
        """Kembalikan unit `RESERVED` milik permintaan itu ke `IN_STOCK`."""
        ...

    def units_for_request(self, db: Session, *, stock_request_no: str) -> list[str]:
        """Nomor seri unit yang terkait permintaan itu."""
        ...

    def mark_with_technician(
        self, db: Session, *, stock_request_no: str, serial_numbers: list[str], technician_employee_id: str
    ) -> list[str]:
        """`RESERVED` -> `WITH_TECHNICIAN`; nomor seri di luar reservasi -> SERIAL_NOT_RESERVED."""
        ...

    def mark_installed(self, db: Session, *, serial_numbers: list[str], ticket_code: str) -> None:
        """`WITH_TECHNICIAN` -> `INSTALLED`."""
        ...

    def mark_returned(self, db: Session, *, serial_numbers: list[str]) -> None:
        """`WITH_TECHNICIAN` -> `RETURNED` (menunggu pemeriksaan)."""
        ...

    def mark_faulty(self, db: Session, *, serial_number: str, notes: str | None = None) -> None:
        """Tandai unit `FAULTY`."""
        ...


class StockRequestPort(Protocol):
    """Diimplementasikan Slice A (SCM-A-09)."""

    def reevaluate_pending(self, db: Session, *, item_sku: str, warehouse_code: str) -> list[str]:
        """Permintaan `PENDING_STOCK` yang kini cukup menjadi `READY_TO_ISSUE`; kembalikan `stock_request_no`-nya."""
        ...


class _Unimplemented:
    def __init__(self, port: str, issue: str) -> None:
        self._port = port
        self._issue = issue

    def __getattr__(self, name: str) -> Any:
        def _fail(*args: Any, **kwargs: Any) -> Any:
            raise NotImplementedError(f"{self._port}.{name} belum diimplementasikan ({self._issue})")

        return _fail


class Ports:
    procurement: ProcurementPort
    assets: AssetPort
    stock_requests: StockRequestPort

    def __init__(self) -> None:
        self.procurement = _Unimplemented("ProcurementPort", "SCM-B-01")  # type: ignore[assignment]
        self.assets = _Unimplemented("AssetPort", "SCM-C-01")  # type: ignore[assignment]
        self.stock_requests = _Unimplemented("StockRequestPort", "SCM-A-09")  # type: ignore[assignment]


ports = Ports()


@contextmanager
def override(
    procurement: ProcurementPort | None = None,
    assets: AssetPort | None = None,
    stock_requests: StockRequestPort | None = None,
) -> Iterator[Ports]:
    """Ganti implementasi port sementara (untuk tes); implementasi semula dipulihkan saat keluar."""
    saved = (ports.procurement, ports.assets, ports.stock_requests)
    if procurement is not None:
        ports.procurement = procurement
    if assets is not None:
        ports.assets = assets
    if stock_requests is not None:
        ports.stock_requests = stock_requests
    try:
        yield ports
    finally:
        ports.procurement, ports.assets, ports.stock_requests = saved

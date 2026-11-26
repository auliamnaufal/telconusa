"""Slice A: permintaan barang, reservasi, pengeluaran, laporan pemakaian."""
from app.core.ports import ports
from app.stock import jobs  # noqa: F401  (mendaftarkan pekerjaan berkala)
from app.stock.service import StockRequestService

ports.stock_requests = StockRequestService()

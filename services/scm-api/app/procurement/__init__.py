"""Slice B: PR, cek anggaran, PO, persetujuan, penerimaan barang."""
from app.core.ports import ports
from app.procurement import jobs  # noqa: F401  (mendaftarkan pekerjaan berkala)
from app.procurement.purchase_requests import ProcurementService

ports.procurement = ProcurementService()

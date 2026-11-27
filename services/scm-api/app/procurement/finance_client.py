"""Klien Finance `POST /api/v1/budgets/check` (kontrak `contracts/openapi/finance.yaml`).

Gagal tertutup: apa pun selain jawaban `200` yang lengkap berarti "tidak terjangkau" (`None`),
dicatat di log, dan tidak pernah dianggap disetujui.
"""
import logging
from dataclasses import dataclass

import httpx

from shared.config import settings
from shared.service_auth import service_headers

from app.core import clock

logger = logging.getLogger("telconusa.scm.procurement")

COST_CENTER = "CC-SCM"
TIMEOUT_SECONDS = 5.0

# Tes menggantinya dengan `httpx.MockTransport`.
transport: httpx.BaseTransport | None = None


@dataclass(frozen=True)
class BudgetResult:
    approved: bool
    remaining: int


def check_budget(amount: int, correlation_id: str) -> BudgetResult | None:
    """Jawaban Finance untuk `amount` rupiah, atau `None` bila Finance tidak terjangkau."""
    url = f"{settings.FINANCE_API_URL.rstrip('/')}/api/v1/budgets/check"
    body = {"cost_center_code": COST_CENTER, "amount": amount, "fiscal_year": clock.current_year()}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, transport=transport) as client:
            response = client.post(url, json=body, headers=service_headers("scm", ["budgets:check"], correlation_id))
        if response.status_code != 200:
            logger.error("Cek anggaran %s gagal: Finance menjawab HTTP %s", correlation_id, response.status_code)
            return None
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("Cek anggaran %s gagal: Finance tidak terjangkau", correlation_id)
        return None

    approved = payload.get("approved") if isinstance(payload, dict) else None
    remaining = payload.get("remaining") if isinstance(payload, dict) else None
    if not isinstance(approved, bool) or not isinstance(remaining, int):
        logger.error("Cek anggaran %s gagal: respons Finance tidak sesuai kontrak", correlation_id)
        return None
    return BudgetResult(approved=approved, remaining=remaining)

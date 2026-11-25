import hashlib
import hmac
import logging
import uuid
from typing import Any

import httpx

from shared.config import settings
from shared.schemas import EventEnvelope, now_wib_iso

logger = logging.getLogger("telconusa.events")

EVENT_SUBSCRIBERS: dict[str, list[str]] = {
    "invoice.requested": [settings.FINANCE_API_URL],
    "invoice.issued": [settings.CRM_API_URL],
    "invoice.paid": [settings.CRM_API_URL],
    "referral.used": [settings.HRM_API_URL],
    "ticket.created": [settings.SCM_API_URL],
    "ticket.assigned": [settings.HRM_API_URL, settings.SCM_API_URL],
    "ticket.resolved": [settings.HRM_API_URL],
    "subscription.activated": [settings.FINANCE_API_URL],
    "stockrequest.ready": [settings.CRM_API_URL],
    "stockrequest.pending": [settings.CRM_API_URL],
    "stock.issued": [settings.CRM_API_URL],
    "ticket.items_reported": [settings.SCM_API_URL],
    "stock.returned": [settings.CRM_API_URL],
    "technician.rated": [settings.HRM_API_URL],
    # HRM -> Finance, owned by the HRM and Finance tracks (not part of the baseline contracts)
    "payroll.approved": [settings.FINANCE_API_URL],
    # LEGACY: delivered until the owning track migrates
    "order.confirmed": [settings.FINANCE_API_URL],
    "order.cancelled": [settings.FINANCE_API_URL, settings.SCM_API_URL],
    "subscription.terminated": [settings.FINANCE_API_URL, settings.SCM_API_URL, settings.HRM_API_URL],
    "workorder.assigned": [settings.SCM_API_URL, settings.HRM_API_URL],
    "workorder.completed": [settings.SCM_API_URL, settings.HRM_API_URL],
    "kit.reconciled": [settings.SCM_API_URL],
    "invoice.overdue": [settings.CRM_API_URL],
    "commission.finalized": [settings.HRM_API_URL],
    "vendor.paid": [settings.SCM_API_URL],
    "payroll.paid": [settings.HRM_API_URL],
    "stock.adjusted": [settings.FINANCE_API_URL],
    "goods.received": [settings.FINANCE_API_URL],
    "po.approved": [settings.FINANCE_API_URL],
    "shipment.delivered": [settings.CRM_API_URL, settings.FINANCE_API_URL],
    "employee.hired": [settings.CRM_API_URL, settings.SCM_API_URL, settings.FINANCE_API_URL],
    "employee.terminated": [settings.CRM_API_URL, settings.SCM_API_URL, settings.FINANCE_API_URL],
}

_rabbitmq_warning_logged = False


def sign_payload(raw_body: bytes) -> str:
    return hmac.new(
        settings.HMAC_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def verify_signature(raw_body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = sign_payload(raw_body)
    return hmac.compare_digest(expected, signature)


def build_envelope(
    event_type: str,
    source: str,
    correlation_id: str,
    data: dict[str, Any],
    event_id: str | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or f"evt_{uuid.uuid4().hex[:12].upper()}",
        event_type=event_type,
        version=1,
        occurred_at=now_wib_iso(),
        source=source,
        correlation_id=correlation_id,
        data=data,
    )


async def deliver(
    envelope: EventEnvelope,
    targets: list[str] | None = None,
    timeout: float = 4.0,
) -> bool:
    """POST the signed envelope to every subscriber; True only if all answered 2xx."""
    if targets is None:
        targets = EVENT_SUBSCRIBERS.get(envelope.event_type, [])
    raw_body = envelope.model_dump_json().encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-TelcoNusa-Signature": sign_payload(raw_body),
        "X-Correlation-Id": envelope.correlation_id,
    }
    all_ok = True
    async with httpx.AsyncClient(timeout=timeout) as client:
        for base_url in targets:
            try:
                response = await client.post(
                    f"{base_url.rstrip('/')}/internal/events",
                    content=raw_body,
                    headers=headers,
                )
                if not response.is_success:
                    all_ok = False
                    logger.warning(
                        "Webhook delivery of %s to %s returned HTTP %s",
                        envelope.event_id,
                        base_url,
                        response.status_code,
                    )
            except Exception as exc:
                all_ok = False
                logger.warning("Webhook delivery to %s failed: %s", base_url, exc)
    return all_ok


async def publish_event(
    event_type: str,
    source: str,
    correlation_id: str,
    data: dict[str, Any],
) -> EventEnvelope:
    global _rabbitmq_warning_logged
    if settings.EVENT_TRANSPORT == "rabbitmq" and not _rabbitmq_warning_logged:
        _rabbitmq_warning_logged = True
        logger.warning("EVENT_TRANSPORT=rabbitmq is deprecated and ignored; using HMAC webhook delivery")

    envelope = build_envelope(event_type, source, correlation_id, data)
    await deliver(envelope)
    return envelope

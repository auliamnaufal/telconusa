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
    "order.confirmed": [settings.FINANCE_API_URL],
    "order.cancelled": [settings.FINANCE_API_URL, settings.SCM_API_URL],
    "subscription.activated": [settings.FINANCE_API_URL],
    "subscription.terminated": [settings.FINANCE_API_URL, settings.SCM_API_URL, settings.HRM_API_URL],
    "workorder.assigned": [settings.SCM_API_URL, settings.HRM_API_URL],
    "workorder.completed": [settings.SCM_API_URL, settings.HRM_API_URL],
    "ticket.resolved": [settings.FINANCE_API_URL, settings.HRM_API_URL],
    "referral.used": [settings.HRM_API_URL],
    "technician.rated": [settings.HRM_API_URL],
    "kit.reconciled": [settings.SCM_API_URL],
    "invoice.issued": [settings.CRM_API_URL],
    "invoice.paid": [settings.CRM_API_URL],
    "invoice.overdue": [settings.CRM_API_URL],
    "commission.finalized": [settings.HRM_API_URL],
    "vendor.paid": [settings.SCM_API_URL],
    "payroll.paid": [settings.HRM_API_URL],
    "stock.issued": [settings.CRM_API_URL, settings.FINANCE_API_URL],
    "stock.adjusted": [settings.FINANCE_API_URL],
    "goods.received": [settings.FINANCE_API_URL],
    "po.approved": [settings.FINANCE_API_URL],
    "shipment.delivered": [settings.CRM_API_URL, settings.FINANCE_API_URL],
    "employee.hired": [settings.CRM_API_URL, settings.SCM_API_URL, settings.FINANCE_API_URL],
    "employee.terminated": [settings.CRM_API_URL, settings.SCM_API_URL, settings.FINANCE_API_URL],
    "payroll.approved": [settings.FINANCE_API_URL],
}


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


async def publish_event(
    event_type: str,
    source: str,
    correlation_id: str,
    data: dict[str, Any],
) -> EventEnvelope:
    envelope = EventEnvelope(
        event_id=f"evt_{uuid.uuid4().hex[:12].upper()}",
        event_type=event_type,
        version=1,
        occurred_at=now_wib_iso(),
        source=source,
        correlation_id=correlation_id,
        data=data,
    )
    raw_body = envelope.model_dump_json().encode("utf-8")

    # 1. Publish to RabbitMQ topic exchange when configured (for Management UI & durability)
    if settings.EVENT_TRANSPORT == "rabbitmq":
        try:
            import aio_pika

            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL, timeout=3)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(
                    "telconusa.events", aio_pika.ExchangeType.TOPIC, durable=True
                )
                message = aio_pika.Message(
                    body=raw_body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=envelope.event_id,
                    correlation_id=correlation_id,
                )
                await exchange.publish(message, routing_key=event_type)
                logger.info("Published %s (%s) to RabbitMQ", event_type, envelope.event_id)
        except Exception as exc:
            logger.warning("RabbitMQ publish failed (%s), continuing with HMAC webhook", exc)

    # 2. Direct HMAC-signed webhook delivery so subscribers react immediately and idempotently
    targets = EVENT_SUBSCRIBERS.get(event_type, [])
    signature = sign_payload(raw_body)
    async with httpx.AsyncClient(timeout=4.0) as client:
        for base_url in targets:
            try:
                await client.post(
                    f"{base_url.rstrip('/')}/internal/events",
                    content=raw_body,
                    headers={
                        "Content-Type": "application/json",
                        "X-TelcoNusa-Signature": signature,
                        "X-Correlation-Id": correlation_id,
                    },
                )
            except Exception as exc:
                logger.warning("Webhook delivery to %s failed: %s", base_url, exc)

    return envelope

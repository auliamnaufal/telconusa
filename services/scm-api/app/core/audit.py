"""Catatan audit untuk operasi tulis SCM."""
import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.auth import Actor
from app.core.models import AuditLog


def record(
    db: Session,
    actor: Actor | str,
    action: str,
    entity: str,
    entity_id: str,
    detail: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> AuditLog:
    """Tambah satu baris audit ke transaksi pemanggil (tanpa commit)."""
    actor_id, role = (actor.sub, actor.role) if isinstance(actor, Actor) else (actor, None)
    row = AuditLog(
        actor=actor_id,
        role=role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=json.dumps(detail, default=str) if detail is not None else None,
        correlation_id=correlation_id,
    )
    db.add(row)
    return row

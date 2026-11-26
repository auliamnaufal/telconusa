"""Idempotensi `POST` transaksi lewat header `Idempotency-Key`.

Pemakaian di endpoint:

    @router.post("/x/{no}/issue")
    def issue(no: str, key: str | None = Depends(idempotency_key), db: Session = Depends(get_db), ...):
        def action() -> tuple[int, dict]:
            ...ubah data tanpa commit...
            return 200, {...}
        status, body = run_idempotent(db, key, f"POST /x/{no}/issue", action)
        return JSONResponse(body, status_code=status)

`run_idempotent` melakukan commit. Pengulangan dengan kunci dan endpoint sama mengembalikan
respons tersimpan tanpa menjalankan `action` lagi.
"""
import json
from typing import Any, Callable

from fastapi import Header
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import IdempotencyKey


def idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    return idempotency_key


def run_idempotent(
    db: Session,
    key: str | None,
    endpoint: str,
    action: Callable[[], tuple[int, dict[str, Any]]],
) -> tuple[int, dict[str, Any]]:
    if not key:
        status, body = action()
        db.commit()
        return status, body

    stored = db.get(IdempotencyKey, (key, endpoint))
    if stored is not None:
        return stored.status_code, json.loads(stored.response_json)

    status, body = action()
    db.add(IdempotencyKey(key=key, endpoint=endpoint, status_code=status, response_json=json.dumps(body, default=str)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        stored = db.get(IdempotencyKey, (key, endpoint))
        if stored is None:
            raise
        return stored.status_code, json.loads(stored.response_json)
    return status, body

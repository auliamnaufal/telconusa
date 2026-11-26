from app.core.idempotency import run_idempotent
from app.core.models import IdempotencyKey


def test_same_key_runs_action_once_and_replays_response(db):
    runs = []

    def action():
        runs.append(1)
        return 201, {"po_no": "PO-2026-0001"}

    first = run_idempotent(db, "key-1", "POST /purchase-orders", action)
    second = run_idempotent(db, "key-1", "POST /purchase-orders", action)

    assert first == second == (201, {"po_no": "PO-2026-0001"})
    assert len(runs) == 1


def test_different_key_or_endpoint_runs_again(db):
    runs = []

    def action():
        runs.append(1)
        return 200, {"n": len(runs)}

    run_idempotent(db, "key-1", "POST /a", action)
    run_idempotent(db, "key-2", "POST /a", action)
    run_idempotent(db, "key-1", "POST /b", action)
    assert len(runs) == 3


def test_without_key_every_call_runs_and_nothing_is_stored(db):
    runs = []

    def action():
        runs.append(1)
        return 200, {}

    run_idempotent(db, None, "POST /a", action)
    run_idempotent(db, None, "POST /a", action)
    assert len(runs) == 2
    assert db.query(IdempotencyKey).count() == 0


def test_failed_action_stores_nothing_so_retry_can_succeed(db):
    state = {"fail": True}

    def action():
        if state["fail"]:
            raise RuntimeError("boom")
        return 200, {"ok": True}

    try:
        run_idempotent(db, "key-1", "POST /a", action)
    except RuntimeError:
        db.rollback()
    state["fail"] = False
    assert run_idempotent(db, "key-1", "POST /a", action) == (200, {"ok": True})

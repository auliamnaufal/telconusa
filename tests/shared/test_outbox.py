import asyncio
import json
from datetime import datetime, timedelta

import pytest

from shared import events, outbox
from shared.outbox import enqueue_event, make_outbox_models, relay_once


@pytest.fixture
def setup(make_base, make_session_factory):
    Base = make_base()
    Outbox, DeadLetter = make_outbox_models(Base)
    return Outbox, DeadLetter, make_session_factory(Base)


def _enqueue(factory, Outbox, event_type="invoice.issued") -> str:
    with factory() as db:
        event_id = enqueue_event(db, Outbox, event_type, "cor-1", {"invoice_no": "INV-1"}, "finance")
        db.commit()
    return event_id


def _patch_deliver(monkeypatch, result: bool | Exception) -> list:
    calls: list = []

    async def fake_deliver(envelope, targets=None, timeout=4.0):
        calls.append((envelope, targets))
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(events, "deliver", fake_deliver)
    return calls


def test_enqueue_adds_pending_row_with_event_id(setup):
    Outbox, _, factory = setup
    event_id = _enqueue(factory, Outbox)
    assert event_id.startswith("evt_") and len(event_id) == 16
    with factory() as db:
        row = db.query(Outbox).one()
        assert (row.event_id, row.status, row.attempts) == (event_id, "PENDING", 0)
        assert json.loads(row.payload_json) == {"invoice_no": "INV-1"}


def test_enqueue_does_not_commit(setup):
    Outbox, _, factory = setup
    with factory() as db:
        enqueue_event(db, Outbox, "invoice.issued", "cor-1", {}, "finance")
        db.rollback()
        assert db.query(Outbox).count() == 0


def test_relay_success_marks_sent_and_uses_stored_event_id(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    event_id = _enqueue(factory, Outbox)
    calls = _patch_deliver(monkeypatch, True)

    sent = asyncio.run(relay_once(factory, Outbox, DeadLetter, now=datetime.utcnow() + timedelta(seconds=5)))

    assert sent == 1
    envelope, targets = calls[0]
    assert envelope.event_id == event_id
    assert envelope.data == {"invoice_no": "INV-1"}
    assert targets == events.EVENT_SUBSCRIBERS["invoice.issued"]
    with factory() as db:
        assert db.query(Outbox).one().status == "SENT"


def test_sent_rows_are_not_redelivered(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    _enqueue(factory, Outbox)
    calls = _patch_deliver(monkeypatch, True)
    later = datetime.utcnow() + timedelta(hours=1)
    assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=later)) == 1
    assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=later)) == 0
    assert len(calls) == 1


def test_event_without_subscribers_is_marked_sent_without_delivery(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    _enqueue(factory, Outbox, event_type="nobody.listens")
    calls = _patch_deliver(monkeypatch, True)
    assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=datetime.utcnow() + timedelta(hours=1))) == 1
    assert calls == []
    with factory() as db:
        assert db.query(Outbox).one().status == "SENT"


def test_not_yet_due_rows_are_skipped(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    _enqueue(factory, Outbox)
    calls = _patch_deliver(monkeypatch, True)
    assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=datetime(2000, 1, 1))) == 0
    assert calls == []


def test_retry_schedule_then_dead_letter_after_fourth_failure(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    event_id = _enqueue(factory, Outbox)
    _patch_deliver(monkeypatch, False)

    now = datetime.utcnow() + timedelta(seconds=5)
    for attempt, delay in enumerate([1, 5, 15], start=1):
        assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=now)) == 0
        with factory() as db:
            row = db.query(Outbox).one()
            assert row.attempts == attempt
            assert row.status == "PENDING"
            assert row.next_attempt_at == now + timedelta(minutes=delay)
            assert row.last_error
        # not due one second before the scheduled time
        assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=row.next_attempt_at - timedelta(seconds=1))) == 0
        with factory() as db:
            assert db.query(Outbox).one().attempts == attempt
        now = row.next_attempt_at

    assert asyncio.run(relay_once(factory, Outbox, DeadLetter, now=now)) == 0
    with factory() as db:
        assert db.query(Outbox).count() == 0
        dead = db.query(DeadLetter).one()
        assert dead.event_id == event_id
        assert dead.attempts == 4
        assert dead.last_error
        assert json.loads(dead.payload_json) == {"invoice_no": "INV-1"}


def test_delivery_exception_counts_as_failure(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    _enqueue(factory, Outbox)
    _patch_deliver(monkeypatch, RuntimeError("boom"))
    asyncio.run(relay_once(factory, Outbox, DeadLetter, now=datetime.utcnow() + timedelta(seconds=5)))
    with factory() as db:
        row = db.query(Outbox).one()
        assert row.attempts == 1
        assert "boom" in row.last_error


def test_run_relay_survives_exceptions(setup, monkeypatch):
    Outbox, DeadLetter, factory = setup
    runs = {"count": 0}

    async def flaky_relay_once(*args, **kwargs):
        runs["count"] += 1
        if runs["count"] == 1:
            raise RuntimeError("transient")
        return 0

    monkeypatch.setattr(outbox, "relay_once", flaky_relay_once)

    async def scenario() -> None:
        task = asyncio.create_task(outbox.run_relay(factory, Outbox, DeadLetter, interval_seconds=0.01))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert runs["count"] >= 2

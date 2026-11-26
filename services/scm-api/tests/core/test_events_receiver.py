import pytest

from app.core import events as core_events


@pytest.fixture
def recorder(monkeypatch):
    calls: list[dict] = []

    def fake_handler(db, envelope):
        calls.append(envelope)

    monkeypatch.setitem(core_events.HANDLERS, "test.happened", fake_handler)
    return calls


def test_unsigned_event_is_rejected_with_standard_error(client):
    response = client.post("/internal/events", content=b'{"event_id":"evt_X","event_type":"test.happened"}')
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_wrong_signature_is_rejected(client, signed_event):
    raw, headers, _ = signed_event("test.happened", {})
    headers["X-TelcoNusa-Signature"] = "0" * 64
    assert client.post("/internal/events", content=raw, headers=headers).status_code == 401


def test_signed_event_runs_handler_once_even_when_delivered_twice(client, signed_event, recorder):
    raw, headers, event_id = signed_event("test.happened", {"x": 1})

    first = client.post("/internal/events", content=raw, headers=headers)
    second = client.post("/internal/events", content=raw, headers=headers)

    assert first.status_code == 200 and first.json()["status"] == "processed"
    assert second.status_code == 200 and second.json()["status"] == "duplicate_ignored"
    assert len(recorder) == 1
    assert recorder[0]["event_id"] == event_id


def test_event_without_handler_is_acknowledged_and_ignored(client, signed_event):
    raw, headers, _ = signed_event("nobody.listens", {})
    response = client.post("/internal/events", content=raw, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_duplicate_handler_registration_is_refused(monkeypatch):
    monkeypatch.setattr(core_events, "HANDLERS", dict(core_events.HANDLERS))
    core_events.handler("dup.event")(lambda db, e: None)
    with pytest.raises(RuntimeError):
        core_events.handler("dup.event")(lambda db, e: None)

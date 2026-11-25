import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.event_receiver import create_events_router, make_processed_event_model
from shared.events import build_envelope, sign_payload

SIGNATURE_HEADER = "X-TelcoNusa-Signature"


@pytest.fixture
def env(make_base, make_session_factory):
    Base = make_base()
    ProcessedEvent = make_processed_event_model(Base)
    factory = make_session_factory(Base)
    seen: list[dict] = []
    state = {"fail": False}

    def get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    def on_invoice_paid(db, event: dict) -> None:
        seen.append(event)
        # a write inside the handler's transaction, so rollback is observable
        db.add(ProcessedEvent(event_id=f"side-{event['event_id']}", event_type="side-effect"))
        if state["fail"]:
            raise RuntimeError("handler failed")

    async def on_async(db, event: dict) -> None:
        seen.append(event)

    app = FastAPI()
    app.include_router(
        create_events_router(get_db, ProcessedEvent, {"invoice.paid": on_invoice_paid, "async.event": on_async})
    )
    client = TestClient(app, raise_server_exceptions=False)
    return client, factory, ProcessedEvent, seen, state


def _body(event_type: str = "invoice.paid", event_id: str = "evt_AAAAAAAAAAAA") -> bytes:
    envelope = build_envelope(event_type, "finance", "cor-1", {"invoice_no": "INV-1"}, event_id=event_id)
    return envelope.model_dump_json().encode("utf-8")


def _post(client, body: bytes, signature: str | None = None, sign: bool = True):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers[SIGNATURE_HEADER] = signature
    elif sign:
        headers[SIGNATURE_HEADER] = sign_payload(body)
    return client.post("/internal/events", content=body, headers=headers)


def test_missing_signature_is_401(env):
    client, _, _, seen, _ = env
    assert _post(client, _body(), sign=False).status_code == 401
    assert seen == []


def test_wrong_signature_is_401(env):
    client, _, _, seen, _ = env
    assert _post(client, _body(), signature="0" * 64).status_code == 401
    assert seen == []


def test_signature_of_other_body_is_401(env):
    client, _, _, _, _ = env
    assert _post(client, _body(), signature=sign_payload(b"other")).status_code == 401


def test_valid_event_is_processed_and_recorded(env):
    client, factory, ProcessedEvent, seen, _ = env
    response = _post(client, _body())
    assert response.status_code == 200
    assert response.json() == {"status": "processed", "event_id": "evt_AAAAAAAAAAAA"}
    assert seen[0]["data"] == {"invoice_no": "INV-1"}
    with factory() as db:
        assert db.get(ProcessedEvent, "evt_AAAAAAAAAAAA").event_type == "invoice.paid"


def test_async_handler_is_awaited(env):
    client, _, _, seen, _ = env
    response = _post(client, _body("async.event", "evt_BBBBBBBBBBBB"))
    assert response.json()["status"] == "processed"
    assert len(seen) == 1


def test_duplicate_event_id_is_ignored(env):
    client, _, _, seen, _ = env
    body = _body()
    assert _post(client, body).json()["status"] == "processed"
    response = _post(client, body)
    assert response.status_code == 200
    assert response.json() == {"status": "duplicate_ignored"}
    assert len(seen) == 1


def test_unknown_event_type_is_ignored_and_recorded(env):
    client, factory, ProcessedEvent, seen, _ = env
    response = _post(client, _body("unknown.type", "evt_CCCCCCCCCCCC"))
    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "event_id": "evt_CCCCCCCCCCCC"}
    assert seen == []
    with factory() as db:
        assert db.get(ProcessedEvent, "evt_CCCCCCCCCCCC") is not None


def test_handler_exception_rolls_back_and_allows_retry(env):
    client, factory, ProcessedEvent, seen, state = env
    body = _body()
    state["fail"] = True
    assert _post(client, body).status_code == 500
    with factory() as db:
        assert db.query(ProcessedEvent).count() == 0

    state["fail"] = False
    response = _post(client, body)
    assert response.json()["status"] == "processed"
    assert len(seen) == 2


def test_invalid_json_is_400(env):
    client, _, _, _, _ = env
    body = b"{not json"
    assert _post(client, body).status_code == 400


@pytest.mark.parametrize("payload", [{"event_type": "invoice.paid"}, {"event_id": "evt_X"}, [1, 2]])
def test_missing_envelope_fields_is_400(env, payload):
    client, _, _, _, _ = env
    assert _post(client, json.dumps(payload).encode("utf-8")).status_code == 400

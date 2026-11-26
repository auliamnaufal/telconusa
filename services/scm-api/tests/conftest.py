import os
import sys
from pathlib import Path

# Secret dan basis data uji diatur sebelum `shared.config` dan `app.database` diimpor.
os.environ["JWT_SECRET"] = "test-jwt-secret-for-scm-tests-0123456789"
os.environ["HMAC_WEBHOOK_SECRET"] = "test-hmac-secret-for-scm-tests-0123456789"
os.environ["DATABASE_URL"] = "sqlite://"

API_DIR = Path(__file__).resolve().parents[1]
SERVICES_DIR = API_DIR.parent
sys.path.insert(0, str(SERVICES_DIR))
sys.path.insert(0, str(API_DIR))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from shared.auth import create_access_token  # noqa: E402
from shared.events import build_envelope, sign_payload  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402  (mengimpor semua model dan router slice)
from app.seed import seed_all  # noqa: E402


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded_db(db):
    seed_all(db)
    db.commit()
    return db


@pytest.fixture
def client(session_factory):
    def _get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    # Tanpa `with`: lifespan (relay outbox) tidak dijalankan.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_token():
    def _make(role: str, sub: str = "EMP-0001", name: str = "Tester") -> str:
        return create_access_token({"sub": sub, "role": role, "name": name})

    return _make


@pytest.fixture
def auth(make_token):
    def _auth(role: str, sub: str = "EMP-0001") -> dict[str, str]:
        return {"Authorization": f"Bearer {make_token(role, sub)}"}

    return _auth


@pytest.fixture
def signed_event():
    """Bangun (isi mentah, header) event bertanda tangan untuk `POST /internal/events`."""

    def _build(event_type: str, data: dict, correlation_id: str = "TKT-000001", event_id: str | None = None, source: str = "crm"):
        envelope = build_envelope(event_type, source, correlation_id, data, event_id=event_id)
        raw = envelope.model_dump_json().encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-TelcoNusa-Signature": sign_payload(raw),
            "X-Correlation-Id": correlation_id,
        }
        return raw, headers, envelope.event_id

    return _build


@pytest.fixture
def validate_event():
    """Periksa `data` event terhadap `contracts/events/<event>.schema.json`."""
    import json

    import jsonschema

    events_dir = API_DIR.parents[1] / "contracts" / "events"

    def _validate(event_type: str, data: dict) -> None:
        schema = json.loads((events_dir / f"{event_type}.schema.json").read_text())
        jsonschema.validate(data, schema)

    return _validate

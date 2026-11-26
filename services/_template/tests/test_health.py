import os

os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("HMAC_WEBHOOK_SECRET", "test-hmac-secret")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

# Tanpa `with`: lifespan (relay outbox) tidak dijalankan, jadi tidak butuh database.
client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_endpoint_requires_token() -> None:
    assert client.get("/api/v1/examples").status_code == 401

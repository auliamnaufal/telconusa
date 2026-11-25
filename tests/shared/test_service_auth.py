import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from shared.auth import create_access_token
from shared.config import settings
from shared.service_auth import (
    create_service_token,
    require_service,
    require_user_or_service,
    service_headers,
)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()

    @app.get("/stock")
    def stock(claims: dict = Depends(require_service("stock:read", "stock:write"))):
        return {"sub": claims["sub"]}

    @app.get("/either")
    def either(claims: dict = Depends(require_user_or_service(("WAREHOUSE_STAFF",), "stock:read"))):
        return {"sub": claims["sub"], "role": claims["role"]}

    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_service_token_claims():
    claims = jwt.decode(
        create_service_token("crm", ["stock:read"], ttl_seconds=60),
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert claims["sub"] == "svc:crm"
    assert claims["role"] == "SERVICE"
    assert claims["scopes"] == ["stock:read"]
    assert claims["exp"] - claims["iat"] == 60


def test_service_headers_with_and_without_correlation_id():
    assert set(service_headers("crm", ["a"])) == {"Authorization"}
    headers = service_headers("crm", ["a"], correlation_id="cor-9")
    assert headers["X-Correlation-Id"] == "cor-9"
    assert headers["Authorization"].startswith("Bearer ")


def test_require_service_missing_token_is_401(client):
    assert client.get("/stock").status_code == 401


def test_require_service_invalid_token_is_401(client):
    assert client.get("/stock", headers=_bearer("not-a-jwt")).status_code == 401


def test_require_service_user_token_is_403(client):
    token = create_access_token({"sub": "u1", "role": "DIRECTOR"})
    assert client.get("/stock", headers=_bearer(token)).status_code == 403


def test_require_service_missing_scope_is_403_and_lists_scope(client):
    response = client.get("/stock", headers=service_headers("crm", ["stock:read"]))
    assert response.status_code == 403
    assert "stock:write" in response.json()["detail"]
    assert "stock:read" not in response.json()["detail"]


def test_require_service_with_all_scopes_is_200(client):
    response = client.get("/stock", headers=service_headers("crm", ["stock:read", "stock:write"]))
    assert response.status_code == 200
    assert response.json() == {"sub": "svc:crm"}


def test_user_or_service_accepts_allowed_user(client):
    token = create_access_token({"sub": "u1", "role": "WAREHOUSE_STAFF"})
    response = client.get("/either", headers=_bearer(token))
    assert response.status_code == 200
    assert response.json()["role"] == "WAREHOUSE_STAFF"


def test_user_or_service_rejects_other_user_role(client):
    token = create_access_token({"sub": "u1", "role": "CS_AGENT"})
    assert client.get("/either", headers=_bearer(token)).status_code == 403


def test_user_or_service_accepts_service_with_scope(client):
    response = client.get("/either", headers=service_headers("crm", ["stock:read"]))
    assert response.status_code == 200
    assert response.json()["role"] == "SERVICE"


def test_user_or_service_rejects_service_without_scope(client):
    assert client.get("/either", headers=service_headers("crm", ["other:read"])).status_code == 403


def test_user_or_service_without_token_is_401(client):
    assert client.get("/either").status_code == 401

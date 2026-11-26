from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import ScmError, install_error_handlers


class Body(BaseModel):
    qty: int


def make_client() -> TestClient:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/scm-error")
    def scm_error():
        raise ScmError("INSUFFICIENT_STOCK", "Stok ONT-01 tidak cukup", 409, {"sku": "ONT-01", "requested": 1, "available": 0})

    @app.get("/scm-error-own-correlation")
    def own_correlation():
        raise ScmError("X", "x", 409, correlation_id="TKT-000009")

    @app.get("/http-error")
    def http_error():
        raise HTTPException(status_code=403, detail="Akses ditolak")

    @app.get("/transition")
    def transition():
        raise HTTPException(
            status_code=409,
            detail={"code": "INVALID_TRANSITION", "message": "A -> B", "details": {"allowed": ["C"]}},
        )

    @app.post("/validated")
    def validated(body: Body):
        return body

    return TestClient(app)


def test_scm_error_uses_standard_format_and_header_correlation_id():
    response = make_client().get("/scm-error", headers={"X-Correlation-Id": "ORD-2026-000123"})
    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "INSUFFICIENT_STOCK",
            "message": "Stok ONT-01 tidak cukup",
            "details": {"sku": "ONT-01", "requested": 1, "available": 0},
            "correlation_id": "ORD-2026-000123",
        }
    }


def test_explicit_correlation_id_wins_over_header():
    response = make_client().get("/scm-error-own-correlation", headers={"X-Correlation-Id": "ignored"})
    assert response.json()["error"]["correlation_id"] == "TKT-000009"


def test_plain_http_exception_is_wrapped():
    response = make_client().get("/http-error")
    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "FORBIDDEN"
    assert error["message"] == "Akses ditolak"


def test_invalid_transition_detail_keeps_its_code_and_details():
    error = make_client().get("/transition").json()["error"]
    assert error["code"] == "INVALID_TRANSITION"
    assert error["details"] == {"allowed": ["C"]}


def test_unknown_route_and_validation_errors_use_standard_format():
    client = make_client()
    assert client.get("/nope").json()["error"]["code"] == "NOT_FOUND"
    response = client.post("/validated", json={"qty": "abc"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["errors"]

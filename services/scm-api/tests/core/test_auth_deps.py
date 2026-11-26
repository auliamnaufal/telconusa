from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from shared.service_auth import create_service_token

from app.core.auth import Actor, require_scm_roles, require_scope
from app.core.errors import install_error_handlers


def make_client() -> TestClient:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/warehouse")
    def warehouse(actor: Actor = Depends(require_scm_roles("SCM_MANAGER", "WAREHOUSE_STAFF"))):
        return {"sub": actor.sub, "role": actor.role}

    @app.get("/default-read")
    def default_read(actor: Actor = Depends(require_scm_roles())):
        return {"role": actor.role}

    @app.get("/stock")
    def stock(_: dict = Depends(require_scope("stock:read"))):
        return {"ok": True}

    return TestClient(app)


def test_user_role_check(auth):
    client = make_client()
    assert client.get("/warehouse").status_code == 401
    assert client.get("/warehouse", headers=auth("CS_AGENT")).status_code == 403
    response = client.get("/warehouse", headers=auth("WAREHOUSE_STAFF", "EMP-0020"))
    assert response.status_code == 200
    assert response.json() == {"sub": "EMP-0020", "role": "WAREHOUSE_STAFF"}


def test_default_roles_are_scm_and_director(auth):
    client = make_client()
    assert client.get("/default-read", headers=auth("DIRECTOR")).status_code == 200
    assert client.get("/default-read", headers=auth("FINANCE_MANAGER")).status_code == 403


def test_service_scope_check(auth):
    client = make_client()
    good = {"Authorization": f"Bearer {create_service_token('crm', ['stock:read'])}"}
    wrong_scope = {"Authorization": f"Bearer {create_service_token('crm', ['packagekits:read'])}"}
    assert client.get("/stock", headers=good).status_code == 200
    assert client.get("/stock", headers=wrong_scope).status_code == 403
    assert client.get("/stock", headers=auth("SCM_MANAGER")).status_code == 403
    assert client.get("/stock").status_code == 401

"""Dependensi peran dan cakupan layanan untuk endpoint SCM."""
from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Depends

from shared.auth import SCM_ROLES, require_roles
from shared.service_auth import require_service

# Kelompok role per jenis operasi (spec bagian 1.2 dan 8).
ROLES_READ = SCM_ROLES  # DIRECTOR, SCM_MANAGER, WAREHOUSE_STAFF, PROCUREMENT_STAFF
ROLES_WAREHOUSE = ("SCM_MANAGER", "WAREHOUSE_STAFF")
ROLES_PROCUREMENT = ("SCM_MANAGER", "PROCUREMENT_STAFF")
ROLES_MANAGER = ("SCM_MANAGER",)
ROLES_APPROVER = ("SCM_MANAGER", "FINANCE_MANAGER", "DIRECTOR")
ROLES_PO_READ = ("DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF", "FINANCE_MANAGER")


@dataclass(frozen=True)
class Actor:
    sub: str
    role: str
    name: str | None = None


def _to_actor(claims: dict[str, Any]) -> Actor:
    return Actor(sub=str(claims.get("sub", "")), role=str(claims.get("role", "")), name=claims.get("name"))


def require_scm_roles(*roles: str) -> Callable[..., Actor]:
    """JWT pengguna dengan salah satu role; tanpa argumen berarti `ROLES_READ`."""
    checker = require_roles(*(roles or ROLES_READ))

    def _dependency(claims: dict[str, Any] = Depends(checker)) -> Actor:
        return _to_actor(claims)

    return _dependency


def require_scope(*scopes: str) -> Callable[..., dict[str, Any]]:
    """Token layanan dengan semua cakupan yang disebut (contoh `stock:read`)."""
    return require_service(*scopes)

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
from fastapi import Depends, Header, HTTPException

from shared.config import settings

EMPLOYEE_ROLES = (
    "DIRECTOR",
    "CRM_MANAGER",
    "CS_AGENT",
    "MARKETING",
    "SALES_EXEC",
    "SALES_MANAGER",
    "TECHNICIAN",
    "HR_MANAGER",
    "HR_STAFF",
    "PAYROLL_STAFF",
    "SCM_MANAGER",
    "WAREHOUSE_STAFF",
    "PROCUREMENT_STAFF",
    "FINANCE_MANAGER",
    "ACCOUNTANT",
    "AR_STAFF",
    "AP_STAFF",
)

CRM_STAFF_ROLES = (
    "DIRECTOR",
    "CRM_MANAGER",
    "CS_AGENT",
    "MARKETING",
    "SALES_EXEC",
    "SALES_MANAGER",
    "TECHNICIAN",
)

HR_ADMIN_ROLES = ("DIRECTOR", "HR_MANAGER", "HR_STAFF", "PAYROLL_STAFF")
SCM_ROLES = ("DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF")
FINANCE_ROLES = ("DIRECTOR", "FINANCE_MANAGER", "ACCOUNTANT", "AR_STAFF", "AP_STAFF")


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return hmac.compare_digest(dk.hex(), expected)


def create_access_token(payload: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    to_encode = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_optional_user(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autentikasi diperlukan (Bearer token tidak ditemukan)")
    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def require_roles(*allowed_roles: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _checker(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Akses ditolak untuk role {user.get('role')}. Role dibutuhkan: {', '.join(allowed_roles)}",
            )
        return user

    return _checker

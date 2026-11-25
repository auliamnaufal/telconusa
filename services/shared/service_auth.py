from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException

from shared.auth import get_current_user
from shared.config import settings

SERVICE_ROLE = "SERVICE"


def create_service_token(service: str, scopes: list[str], ttl_seconds: int = 300) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"svc:{service}",
        "role": SERVICE_ROLE,
        "scopes": list(scopes),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def service_headers(service: str, scopes: list[str], correlation_id: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {create_service_token(service, scopes)}"}
    if correlation_id:
        headers["X-Correlation-Id"] = correlation_id
    return headers


def _check_service_claims(claims: dict[str, Any], scopes: tuple[str, ...]) -> None:
    if claims.get("role") != SERVICE_ROLE:
        raise HTTPException(status_code=403, detail="Endpoint ini hanya untuk token service")
    missing = [scope for scope in scopes if scope not in claims.get("scopes", [])]
    if missing:
        raise HTTPException(status_code=403, detail=f"Scope service kurang: {', '.join(missing)}")


def require_service(*scopes: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _checker(claims: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        _check_service_claims(claims, scopes)
        return claims

    return _checker


def require_user_or_service(user_roles: tuple[str, ...], *scopes: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _checker(claims: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if claims.get("role") == SERVICE_ROLE:
            _check_service_claims(claims, scopes)
        elif claims.get("role") not in user_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Akses ditolak untuk role {claims.get('role')}. Role dibutuhkan: {', '.join(user_roles)}",
            )
        return claims

    return _checker

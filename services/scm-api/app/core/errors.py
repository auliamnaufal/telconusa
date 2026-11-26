"""Galat SCM dalam format baku `contracts/variable_standards.md` bagian 1."""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
}


class ScmError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 409,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}
        self.correlation_id = correlation_id


def error_body(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "correlation_id": correlation_id,
        }
    }


def _correlation_id(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ScmError)
    async def _scm_error(request: Request, exc: ScmError) -> JSONResponse:
        body = error_body(exc.code, exc.message, exc.details, exc.correlation_id or _correlation_id(request))
        return JSONResponse(status_code=exc.status, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            body = error_body(
                str(detail["code"]),
                str(detail.get("message", "")),
                detail.get("details"),
                _correlation_id(request),
            )
        else:
            code = _STATUS_CODES.get(exc.status_code, f"HTTP_{exc.status_code}")
            body = error_body(code, str(detail), None, _correlation_id(request))
        return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = error_body(
            "VALIDATION_ERROR",
            "Data permintaan tidak valid",
            {"errors": jsonable_encoder(exc.errors())},
            _correlation_id(request),
        )
        return JSONResponse(status_code=422, content=body)

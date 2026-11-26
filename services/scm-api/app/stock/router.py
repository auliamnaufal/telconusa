"""Endpoint HTTP Slice A. Diisi oleh issue slice ini."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["stock"])

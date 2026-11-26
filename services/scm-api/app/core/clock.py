"""Waktu terpusat supaya tes bisa mengatur jam (`monkeypatch.setattr(clock, "utcnow", ...)`).

Basis data menyimpan UTC tanpa zona; API dan event memakai ISO 8601 `+07:00` lewat `to_wib_iso`.
"""
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_wib_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).astimezone(WIB).isoformat(timespec="seconds")


def current_year() -> int:
    return datetime.now(WIB).year

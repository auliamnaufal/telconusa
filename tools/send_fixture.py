#!/usr/bin/env python3
"""POST a signed event fixture to a service's /internal/events endpoint.

Usage: python tools/send_fixture.py <event.type> --to http://localhost:8004
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "contracts" / "examples" / "events"


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def build_body(envelope: dict, keep_id: bool) -> bytes:
    if not keep_id:
        envelope = {**envelope, "event_id": f"evt_{uuid.uuid4().hex[:12].upper()}"}
    return json.dumps(envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def post(url: str, body: bytes, signature: str, correlation_id: str) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-TelcoNusa-Signature": signature,
            "X-Correlation-Id": correlation_id,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_type", help="event type, e.g. invoice.requested")
    parser.add_argument("--to", required=True, help="service base URL, e.g. http://localhost:8004")
    parser.add_argument("--secret", default="HMAC_WEBHOOK_SECRET", help="name of the environment variable holding the HMAC secret")
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--keep-id", action="store_true", help="keep the fixture's event_id instead of generating a fresh one")
    args = parser.parse_args(argv)

    secret = os.environ.get(args.secret)
    if not secret:
        print(f"ERROR: environment variable {args.secret} is not set", file=sys.stderr)
        return 1
    fixture = args.fixture_dir / f"{args.event_type}.json"
    if not fixture.is_file():
        print(f"ERROR: fixture not found: {fixture}", file=sys.stderr)
        return 1

    envelope = json.loads(fixture.read_text(encoding="utf-8"))
    body = build_body(envelope, args.keep_id)
    url = f"{args.to.rstrip('/')}/internal/events"
    try:
        status, text = post(url, body, sign(body, secret), str(envelope.get("correlation_id", "")))
    except urllib.error.URLError as exc:
        print(f"ERROR: cannot reach {url}: {exc.reason}", file=sys.stderr)
        return 1
    print(f"POST {url} -> {status}")
    print(text)
    return 1 if status >= 400 else 0


if __name__ == "__main__":
    sys.exit(main())

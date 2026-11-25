#!/usr/bin/env python3
"""Validate cross-track contracts and generate tracks/STATUS.md.

Usage: python tools/check_contracts.py [--root PATH] [--check]

Reads contracts/openapi, contracts/events, contracts/examples/events and
tracks/*.md, reports every inconsistency as `ERROR: <file>: <message>` and
exits 1 if any was found. Without --check it (re)writes tracks/STATUS.md;
with --check it fails when that file is stale.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

STATUSES = ("PLANNED", "MOCKED", "LIVE", "CHANGING", "DEPRECATED")
INTEGRATED = ("LIVE", "MOCKED")
AUTH_MODES = ("public", "user", "service")
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
ENVELOPE_KEYS = ("event_id", "event_type", "version", "occurred_at", "source", "correlation_id", "data")
TRACK_KEYS = ("track", "owner_team", "folders", "owns", "provides", "consumes")
FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
STATUS_FILE = "tracks/STATUS.md"

Item = dict[str, Any]


class Contracts:
    """In-memory view of everything under contracts/ and tracks/."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.errors: list[str] = []
        self.tracks: dict[str, dict[str, Any]] = {}
        self.track_names: set[str] = set()
        self.ops: dict[str, dict[str, Item]] = {}
        self.events: dict[str, Item] = {}
        self.examples: dict[str, Any] = {}

    def error(self, where: Path | str, message: str) -> None:
        path = Path(where)
        rel = path.relative_to(self.root).as_posix() if path.is_absolute() else str(where)
        self.errors.append(f"ERROR: {rel}: {message}")

    def items(self, track: str, section: str, kind: str) -> list[Item]:
        block = self.tracks.get(track, {}).get(section) or {}
        entries = block.get(kind) if isinstance(block, dict) else None
        return [e for e in entries or [] if isinstance(e, dict) and "id" in e]

    def provided(self, track: str, kind: str, item_id: str) -> Item | None:
        return next((e for e in self.items(track, "provides", kind) if e["id"] == item_id), None)

    def consumed(self, track: str, kind: str, provider: str, item_id: str) -> Item | None:
        return next(
            (e for e in self.items(track, "consumes", kind) if e["id"] == item_id and e.get("from") == provider),
            None,
        )


# --------------------------------------------------------------------------- loading


def load_tracks(c: Contracts) -> None:
    for path in sorted((c.root / "tracks").glob("*.md")):
        if path.name.startswith("_") or path.name == "STATUS.md":
            continue
        c.track_names.add(path.stem)
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            c.error(path, "missing YAML front matter between '---' lines")
            continue
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            c.error(path, f"front matter is not valid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            c.error(path, "front matter must be a mapping")
            continue
        c.tracks[path.stem] = data


def load_openapi(c: Contracts) -> None:
    for path in sorted((c.root / "contracts" / "openapi").glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            c.error(path, f"invalid YAML: {exc}")
            continue
        ops: dict[str, Item] = {}
        for route, methods in ((doc or {}).get("paths") or {}).items():
            for method, op in (methods or {}).items():
                if method in HTTP_METHODS and isinstance(op, dict):
                    ops[f"{method.upper()} {route}"] = op
        c.ops[path.stem] = ops


def load_json(c: Contracts, path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        c.error(path, f"invalid JSON: {exc}")
        return None


def load_events(c: Contracts) -> None:
    for path in sorted((c.root / "contracts" / "events").glob("*.schema.json")):
        schema = load_json(c, path)
        if schema is not None:
            c.events[path.name.removesuffix(".schema.json")] = schema
    for path in sorted((c.root / "contracts" / "examples" / "events").glob("*.json")):
        example = load_json(c, path)
        if example is not None:
            c.examples[path.stem] = example


# ------------------------------------------------------------------------ validation


def check_track_structure(c: Contracts) -> None:
    for name, data in c.tracks.items():
        where = f"tracks/{name}.md"
        missing = [k for k in TRACK_KEYS if k not in data]
        if missing:
            c.error(where, f"front matter missing keys: {', '.join(missing)}")
        if data.get("track") != name:
            c.error(where, f"track is {data.get('track')!r} but file name says {name!r}")
        folders = data.get("folders")
        if not isinstance(folders, list):
            c.error(where, "folders must be a list")
        else:
            for folder in folders:
                if not (c.root / str(folder)).exists():
                    c.error(where, f"folder does not exist: {folder}")
        for section in ("provides", "consumes"):
            check_section(c, name, section)


def check_section(c: Contracts, track: str, section: str) -> None:
    where = f"tracks/{track}.md"
    block = c.tracks[track].get(section)
    if not isinstance(block, dict) or not all(k in block for k in ("api", "events")):
        c.error(where, f"{section} must be a mapping with keys api and events")
        return
    for kind in ("api", "events"):
        entries = block[kind]
        if not isinstance(entries, list):
            c.error(where, f"{section}.{kind} must be a list")
            continue
        for entry in entries:
            check_entry(c, track, section, kind, entry)


def check_entry(c: Contracts, track: str, section: str, kind: str, entry: Any) -> None:
    where = f"tracks/{track}.md"
    if not isinstance(entry, dict) or "id" not in entry:
        c.error(where, f"{section}.{kind} entry without id: {entry!r}")
        return
    label = f"{section}.{kind} {entry['id']}"
    if entry.get("status") not in STATUSES:
        c.error(where, f"{label}: status {entry.get('status')!r} not in {', '.join(STATUSES)}")
    if section == "consumes" and entry.get("from") not in c.track_names:
        c.error(where, f"{label}: unknown provider track {entry.get('from')!r}")
    if section != "provides":
        return
    test = entry.get("test")
    if entry.get("status") == "LIVE" and not test:
        c.error(where, f"{label}: status LIVE requires a test path")
    elif test and not (c.root / str(test)).is_file():
        c.error(where, f"{label}: test file does not exist: {test}")


def check_openapi(c: Contracts) -> None:
    for track, ops in c.ops.items():
        where = f"contracts/openapi/{track}.yaml"
        if track not in c.track_names:
            c.error(where, f"no tracks/{track}.md for this OpenAPI file")
        for op_id, op in ops.items():
            check_operation(c, where, op_id, op)


def check_operation(c: Contracts, where: str, op_id: str, op: Item) -> None:
    if not op.get("operationId"):
        c.error(where, f"{op_id}: missing operationId")
    auth = op.get("x-auth")
    if auth not in AUTH_MODES:
        c.error(where, f"{op_id}: x-auth must be one of {', '.join(AUTH_MODES)}, got {auth!r}")
    if auth == "service" and not op.get("x-scope"):
        c.error(where, f"{op_id}: x-auth=service requires x-scope")
    if auth == "user" and not op.get("x-roles"):
        c.error(where, f"{op_id}: x-auth=user requires non-empty x-roles")
    check_consumer_names(c, where, op_id, op.get("x-consumers"))


def check_consumer_names(c: Contracts, where: str, label: str, consumers: Any) -> None:
    if not isinstance(consumers, list):
        c.error(where, f"{label}: x-consumers must be a list")
        return
    for consumer in consumers:
        if consumer not in c.track_names:
            c.error(where, f"{label}: x-consumers has unknown track {consumer!r}")


def check_events(c: Contracts) -> None:
    for event_id, schema in c.events.items():
        where = f"contracts/events/{event_id}.schema.json"
        publisher = schema.get("x-publisher")
        if publisher not in c.track_names:
            c.error(where, f"x-publisher {publisher!r} is not a known track")
        check_consumer_names(c, where, event_id, schema.get("x-consumers"))
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            c.error(where, f"not a valid JSON Schema: {getattr(exc, 'message', exc)}")
            continue
        check_example(c, event_id, schema)


def check_example(c: Contracts, event_id: str, schema: Item) -> None:
    where = f"contracts/examples/events/{event_id}.json"
    envelope = c.examples.get(event_id)
    if envelope is None:
        if not (c.root / where).exists():
            c.error(where, f"missing example envelope for event {event_id}")
        return
    if not isinstance(envelope, dict):
        c.error(where, "example must be a JSON object envelope")
        return
    missing = [k for k in ENVELOPE_KEYS if k not in envelope]
    if missing:
        c.error(where, f"envelope missing keys: {', '.join(missing)}")
    if envelope.get("event_type") != event_id:
        c.error(where, f"event_type is {envelope.get('event_type')!r}, expected {event_id!r}")
    if "data" in envelope:
        for err in Draft202012Validator(schema).iter_errors(envelope["data"]):
            location = "/".join(str(p) for p in err.absolute_path) or "<root>"
            c.error(where, f"data does not match schema at {location}: {err.message}")


def check_provides(c: Contracts) -> None:
    for track in sorted(c.tracks):
        where = f"tracks/{track}.md"
        listed_api = {e["id"] for e in c.items(track, "provides", "api")}
        for api_id in sorted(listed_api - set(c.ops.get(track, {}))):
            c.error(where, f"provides.api {api_id} is not an operation in contracts/openapi/{track}.yaml")
        for api_id in sorted(set(c.ops.get(track, {})) - listed_api):
            c.error(where, f"operation {api_id} in contracts/openapi/{track}.yaml is not listed in provides.api")

        listed_events = {e["id"] for e in c.items(track, "provides", "events")}
        published = {i for i, s in c.events.items() if s.get("x-publisher") == track}
        for event_id in sorted(listed_events):
            schema = c.events.get(event_id)
            if schema is None:
                c.error(where, f"provides.events {event_id} has no contracts/events/{event_id}.schema.json")
            elif schema.get("x-publisher") != track:
                c.error(where, f"provides.events {event_id} has x-publisher {schema.get('x-publisher')!r}")
        for event_id in sorted(published - listed_events):
            c.error(where, f"event {event_id} (x-publisher {track}) is not listed in provides.events")


def check_consumes(c: Contracts) -> None:
    for track in sorted(c.tracks):
        for entry in c.items(track, "consumes", "api"):
            check_consumed(c, track, "api", entry)
        for entry in c.items(track, "consumes", "events"):
            check_consumed(c, track, "events", entry)


def check_consumed(c: Contracts, track: str, kind: str, entry: Item) -> None:
    where = f"tracks/{track}.md"
    provider, item_id = entry.get("from"), entry["id"]
    if provider not in c.track_names:
        return
    if kind == "api":
        declaration = c.ops.get(provider, {}).get(item_id)
        if declaration is None:
            c.error(where, f"consumes.api {item_id}: not an operation in contracts/openapi/{provider}.yaml")
            return
    else:
        declaration = c.events.get(item_id)
        if declaration is None:
            c.error(where, f"consumes.events {item_id}: no contracts/events/{item_id}.schema.json")
            return
        if declaration.get("x-publisher") != provider:
            c.error(where, f"consumes.events {item_id}: x-publisher is {declaration.get('x-publisher')!r}, not {provider!r}")
    if track not in (declaration.get("x-consumers") or []):
        c.error(where, f"consumes.{kind} {item_id}: {track} is not listed in x-consumers of the contract")
    provided = c.provided(provider, kind, item_id)
    if provided and provided.get("status") == "PLANNED" and entry.get("status") in INTEGRATED:
        c.error(where, f"consumes.{kind} {item_id}: integrated against {provider} but provider status is PLANNED")


def check_declared_consumers(c: Contracts) -> None:
    for provider, ops in c.ops.items():
        for op_id, op in ops.items():
            undeclared_consumers(c, f"contracts/openapi/{provider}.yaml", "api", provider, op_id, op)
    for event_id, schema in c.events.items():
        provider = schema.get("x-publisher")
        where = f"contracts/events/{event_id}.schema.json"
        undeclared_consumers(c, where, "events", provider, event_id, schema)


def undeclared_consumers(c: Contracts, where: str, kind: str, provider: str, item_id: str, declaration: Item) -> None:
    consumers = declaration.get("x-consumers")
    for consumer in consumers if isinstance(consumers, list) else []:
        if consumer in c.tracks and not c.consumed(consumer, kind, provider, item_id):
            c.error(where, f"{item_id}: consumer {consumer} not declared in tracks/{consumer}.md")


# ----------------------------------------------------------------------- STATUS.md


def render_status(c: Contracts) -> str:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for track in sorted(c.tracks):
        for kind, label in (("api", "API"), ("events", "Event")):
            for item in c.items(track, "provides", kind):
                rows.append((track, label, str(item["id"]), str(item.get("status", "")), str(item.get("since") or "-"), consumers_cell(c, kind, track, item["id"])))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))

    lines = [
        "# Contract Status",
        "",
        "> Generated by `python tools/check_contracts.py`. Do not edit by hand; edit `tracks/<track>.md` and regenerate.",
        "",
        "## Legend",
        "",
        "| Status | Meaning |",
        "| --- | --- |",
        "| PLANNED | Agreed in the contract, not implemented yet |",
        "| MOCKED | Consumer integrates against a mock of the contract |",
        "| LIVE | Implemented by the provider and covered by a test |",
        "| CHANGING | Breaking change in progress, consumers must follow the contract diff |",
        "| DEPRECATED | Still served, scheduled for removal |",
        "",
        "Consumers are shown as `track:status` using the status each consumer declares in its own track file.",
        "",
        "## Provided contracts",
        "",
        "| Track | Type | Id | Status | Since | Consumers |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines += [f"| {t} | {k} | `{i}` | {s} | {since} | {cons} |" for t, k, i, s, since, cons in rows]
    lines += ["", "## Summary per track", "", "| Track | " + " | ".join(STATUSES) + " | Total |", "| --- |" + " --- |" * (len(STATUSES) + 1)]
    for track in sorted(c.tracks):
        counts = [sum(1 for r in rows if r[0] == track and r[3] == s) for s in STATUSES]
        lines.append(f"| {track} | " + " | ".join(str(n) for n in counts) + f" | {sum(1 for r in rows if r[0] == track)} |")
    return "\n".join(lines) + "\n"


def consumers_cell(c: Contracts, kind: str, provider: str, item_id: str) -> str:
    declared = [
        f"{t}:{e.get('status', '?')}"
        for t in sorted(c.tracks)
        if (e := c.consumed(t, kind, provider, item_id))
    ]
    return ", ".join(declared) or "-"


def check_status_file(c: Contracts, write: bool) -> None:
    path = c.root / STATUS_FILE
    content = render_status(c)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    elif not path.is_file() or path.read_text(encoding="utf-8") != content:
        c.errors.append(f"ERROR: {STATUS_FILE} is out of date; run python tools/check_contracts.py")


# ---------------------------------------------------------------------------- main


def run(root: Path, check: bool) -> list[str]:
    c = Contracts(root.resolve())
    load_tracks(c)
    load_openapi(c)
    load_events(c)
    check_track_structure(c)
    check_openapi(c)
    check_events(c)
    check_provides(c)
    check_consumes(c)
    check_declared_consumers(c)
    check_status_file(c, write=not check)
    return c.errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent, help="repository root")
    parser.add_argument("--check", action="store_true", help="do not write tracks/STATUS.md; fail if it is stale")
    args = parser.parse_args(argv)
    errors = run(args.root, args.check)
    for line in errors:
        print(line)
    if errors:
        print(f"{len(errors)} contract error(s) found", file=sys.stderr)
        return 1
    print("Contracts OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

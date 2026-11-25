import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "check_contracts.py"
CATALOG = "GET /api/v1/catalog"


def make_tracks() -> dict[str, dict[str, Any]]:
    return {
        "crm": {
            "track": "crm",
            "owner_team": "Team CRM",
            "folders": ["services/crm-api"],
            "owns": [{"entity": "Order", "id_format": "ORD-2026-000001"}],
            "provides": {
                "api": [{"id": CATALOG, "status": "LIVE", "since": "2026-11-25", "test": "services/crm-api/tests/test_catalog.py"}],
                "events": [],
            },
            "consumes": {
                "api": [],
                "events": [{"id": "invoice.issued", "from": "finance", "status": "MOCKED"}],
            },
        },
        "finance": {
            "track": "finance",
            "owner_team": "Team Finance",
            "folders": ["services/finance-api"],
            "owns": [{"entity": "Invoice", "id_format": "INV-2026-000001"}],
            "provides": {
                "api": [],
                "events": [{"id": "invoice.issued", "status": "LIVE", "test": "services/finance-api/tests/test_invoice.py"}],
            },
            "consumes": {
                "api": [{"id": CATALOG, "from": "crm", "status": "MOCKED"}],
                "events": [],
            },
        },
    }


def make_openapi() -> dict[str, Any]:
    operation = {
        "operationId": "listCatalog",
        "x-auth": "user",
        "x-roles": ["admin"],
        "x-consumers": ["finance"],
        "responses": {"200": {"description": "ok"}},
    }
    return {
        "openapi": "3.0.3",
        "info": {"title": "crm", "version": "1"},
        "paths": {"/api/v1/catalog": {"get": operation}},
    }


def make_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["invoice_number", "total"],
        "properties": {"invoice_number": {"type": "string"}, "total": {"type": "integer"}},
        "x-publisher": "finance",
        "x-consumers": ["crm"],
    }


def make_example() -> dict[str, Any]:
    return {
        "event_id": "evt_000000000001",
        "event_type": "invoice.issued",
        "version": 1,
        "occurred_at": "2026-11-25T10:00:00+07:00",
        "source": "finance",
        "correlation_id": "corr-1",
        "data": {"invoice_number": "INV-2026-000001", "total": 100000},
    }


class Tree:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.tracks = make_tracks()
        self.openapi = make_openapi()
        self.schema = make_schema()
        self.example = make_example()

    def write(self) -> None:
        for folder in ("services/crm-api/tests", "services/finance-api/tests", "contracts/openapi", "contracts/events", "contracts/examples/events", "tracks"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        for test in ("services/crm-api/tests/test_catalog.py", "services/finance-api/tests/test_invoice.py"):
            (self.root / test).write_text("", encoding="utf-8")
        for name, front in self.tracks.items():
            body = yaml.safe_dump(front, sort_keys=False)
            (self.root / "tracks" / f"{name}.md").write_text(f"---\n{body}---\n\n# {name}\n", encoding="utf-8")
        (self.root / "tracks" / "_template.md").write_text("---\ntrack: TEMPLATE\n---\n", encoding="utf-8")
        (self.root / "contracts/openapi/crm.yaml").write_text(yaml.safe_dump(self.openapi), encoding="utf-8")
        (self.root / "contracts/events/invoice.issued.schema.json").write_text(json.dumps(self.schema), encoding="utf-8")
        (self.root / "contracts/examples/events/invoice.issued.json").write_text(json.dumps(self.example), encoding="utf-8")

    def run(self, mod: Any, check: bool = False) -> list[str]:
        self.write()
        return mod.run(self.root, check)


@pytest.fixture
def tree(tmp_path: Path) -> Tree:
    return Tree(tmp_path)


def assert_error(errors: list[str], *fragments: str) -> None:
    assert any(all(f in e for f in fragments) for e in errors), errors


def test_valid_tree_passes_and_status_is_stable(tree: Tree, check_contracts: Any) -> None:
    assert tree.run(check_contracts) == []
    status = (tree.root / "tracks/STATUS.md").read_text(encoding="utf-8")
    assert f"| crm | API | `{CATALOG}` | LIVE | 2026-11-25 | finance:MOCKED |" in status
    assert "| finance | Event | `invoice.issued` | LIVE | - | crm:MOCKED |" in status
    assert tree.run(check_contracts, check=True) == []


def test_provided_id_missing_from_openapi(tree: Tree, check_contracts: Any) -> None:
    tree.tracks["crm"]["provides"]["api"].append({"id": "GET /api/v1/ghost", "status": "PLANNED"})
    assert_error(tree.run(check_contracts), "tracks/crm.md", "GET /api/v1/ghost", "not an operation")


def test_orphan_openapi_operation(tree: Tree, check_contracts: Any) -> None:
    orphan = copy.deepcopy(tree.openapi["paths"]["/api/v1/catalog"]["get"])
    orphan.update({"operationId": "createOrder", "x-consumers": []})
    tree.openapi["paths"]["/api/v1/orders"] = {"post": orphan}
    assert_error(tree.run(check_contracts), "POST /api/v1/orders", "not listed in provides.api")


def test_live_without_test(tree: Tree, check_contracts: Any) -> None:
    del tree.tracks["crm"]["provides"]["api"][0]["test"]
    assert_error(tree.run(check_contracts), "tracks/crm.md", "LIVE requires a test path")


def test_live_with_missing_test_file(tree: Tree, check_contracts: Any) -> None:
    tree.tracks["crm"]["provides"]["api"][0]["test"] = "services/crm-api/tests/nope.py"
    assert_error(tree.run(check_contracts), "test file does not exist")


def test_event_example_failing_schema(tree: Tree, check_contracts: Any) -> None:
    tree.example["data"]["total"] = "not-a-number"
    assert_error(tree.run(check_contracts), "contracts/examples/events/invoice.issued.json", "does not match schema")


def test_undeclared_consumer(tree: Tree, check_contracts: Any) -> None:
    tree.tracks["finance"]["consumes"]["api"] = []
    assert_error(tree.run(check_contracts), "consumer finance not declared in tracks/finance.md")


def test_consumed_against_planned_provider(tree: Tree, check_contracts: Any) -> None:
    tree.tracks["crm"]["provides"]["api"][0].update({"status": "PLANNED"})
    del tree.tracks["crm"]["provides"]["api"][0]["test"]
    assert_error(tree.run(check_contracts), "tracks/finance.md", "integrated against crm but provider status is PLANNED")


def test_service_operation_requires_scope(tree: Tree, check_contracts: Any) -> None:
    operation = tree.openapi["paths"]["/api/v1/catalog"]["get"]
    operation["x-auth"] = "service"
    assert_error(tree.run(check_contracts), "x-auth=service requires x-scope")


def test_invalid_status_value(tree: Tree, check_contracts: Any) -> None:
    tree.tracks["finance"]["consumes"]["api"][0]["status"] = "DONE"
    assert_error(tree.run(check_contracts), "tracks/finance.md", "status 'DONE'")


def test_stale_status_fails_check_mode(tree: Tree, check_contracts: Any) -> None:
    assert tree.run(check_contracts) == []
    (tree.root / "tracks/STATUS.md").write_text("stale\n", encoding="utf-8")
    errors = check_contracts.run(tree.root, True)
    assert "ERROR: tracks/STATUS.md is out of date; run python tools/check_contracts.py" in errors
    assert (tree.root / "tracks/STATUS.md").read_text(encoding="utf-8") == "stale\n"


def test_cli_with_root(tree: Tree) -> None:
    tree.write()
    command = [sys.executable, str(SCRIPT), "--root", str(tree.root)]
    assert subprocess.run([*command, "--check"], capture_output=True, text=True).returncode == 1
    assert subprocess.run(command, capture_output=True, text=True).returncode == 0
    assert subprocess.run([*command, "--check"], capture_output=True, text=True).returncode == 0

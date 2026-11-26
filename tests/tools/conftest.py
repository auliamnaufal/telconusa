import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"


def load_tool(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def check_contracts() -> ModuleType:
    return load_tool("check_contracts")


@pytest.fixture(scope="session")
def attribution() -> ModuleType:
    return load_tool("check_agent_attribution")

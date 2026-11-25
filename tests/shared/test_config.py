import os
import subprocess
import sys
from pathlib import Path

import pytest

SERVICES_DIR = Path(__file__).resolve().parents[2] / "services"

GOOD_JWT = "a-real-jwt-secret-value-0123456789"
GOOD_HMAC = "a-real-hmac-secret-value-0123456789"


def _import_config(env: dict[str, str]) -> subprocess.CompletedProcess:
    clean_env = {k: v for k, v in os.environ.items() if k not in ("JWT_SECRET", "HMAC_WEBHOOK_SECRET")}
    clean_env.update(env)
    clean_env["PYTHONPATH"] = str(SERVICES_DIR)
    return subprocess.run(
        [sys.executable, "-c", "import shared.config"],
        env=clean_env,
        capture_output=True,
        text=True,
    )


def test_config_accepts_real_secrets():
    result = _import_config({"JWT_SECRET": GOOD_JWT, "HMAC_WEBHOOK_SECRET": GOOD_HMAC})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("missing", ["JWT_SECRET", "HMAC_WEBHOOK_SECRET"])
def test_config_rejects_unset_secret(missing):
    env = {"JWT_SECRET": GOOD_JWT, "HMAC_WEBHOOK_SECRET": GOOD_HMAC}
    del env[missing]
    result = _import_config(env)
    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert missing in result.stderr
    assert "tools/setup-env.sh" in result.stderr


@pytest.mark.parametrize(
    "placeholder",
    [
        "",
        "   ",
        "change-this-super-secret-jwt-key-in-production",
        "change-this-hmac-webhook-secret",
        "changeme",
        "secret",
    ],
)
def test_config_rejects_blank_or_placeholder_secret(placeholder):
    result = _import_config({"JWT_SECRET": placeholder, "HMAC_WEBHOOK_SECRET": GOOD_HMAC})
    assert result.returncode != 0
    assert "JWT_SECRET" in result.stderr


def test_default_event_transport_is_webhook():
    from shared.config import settings

    assert settings.EVENT_TRANSPORT == "webhook"

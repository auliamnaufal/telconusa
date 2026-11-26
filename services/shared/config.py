import os

PLACEHOLDER_SECRETS = frozenset(
    {
        "change-this-super-secret-jwt-key-in-production",
        "change-this-hmac-webhook-secret",
        "changeme",
        "secret",
    }
)


def _require_secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.lower() in PLACEHOLDER_SECRETS:
        raise RuntimeError(
            f"{name} belum diatur atau masih berisi nilai placeholder. "
            f"Jalankan tools/setup-env.sh atau set variabel lingkungan {name} dengan nilai rahasia yang kuat."
        )
    return value


class Settings:
    JWT_SECRET: str = _require_secret("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
    HMAC_WEBHOOK_SECRET: str = _require_secret("HMAC_WEBHOOK_SECRET")

    EVENT_TRANSPORT: str = os.getenv("EVENT_TRANSPORT", "webhook").lower()

    CRM_API_URL: str = os.getenv("CRM_API_URL", "http://localhost:8001")
    HRM_API_URL: str = os.getenv("HRM_API_URL", "http://localhost:8002")
    SCM_API_URL: str = os.getenv("SCM_API_URL", "http://localhost:8003")
    FINANCE_API_URL: str = os.getenv("FINANCE_API_URL", "http://localhost:8004")

    PPN_RATE: float = float(os.getenv("PPN_RATE", "0.11"))
    REFERRAL_INCENTIVE_RATE: float = float(os.getenv("REFERRAL_INCENTIVE_RATE", "0.10"))
    REFERRAL_KPI_POINTS: int = int(os.getenv("REFERRAL_KPI_POINTS", "10"))


settings = Settings()

import os


class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-super-secret-jwt-key-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
    HMAC_WEBHOOK_SECRET: str = os.getenv("HMAC_WEBHOOK_SECRET", "change-this-hmac-webhook-secret")

    EVENT_TRANSPORT: str = os.getenv("EVENT_TRANSPORT", "rabbitmq").lower()
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://telconusa:telconusa123@localhost:5672/")

    CRM_API_URL: str = os.getenv("CRM_API_URL", "http://localhost:8001")
    HRM_API_URL: str = os.getenv("HRM_API_URL", "http://localhost:8002")
    SCM_API_URL: str = os.getenv("SCM_API_URL", "http://localhost:8003")
    FINANCE_API_URL: str = os.getenv("FINANCE_API_URL", "http://localhost:8004")

    PPN_RATE: float = float(os.getenv("PPN_RATE", "0.11"))
    REFERRAL_INCENTIVE_RATE: float = float(os.getenv("REFERRAL_INCENTIVE_RATE", "0.10"))
    REFERRAL_KPI_POINTS: int = int(os.getenv("REFERRAL_KPI_POINTS", "10"))


settings = Settings()

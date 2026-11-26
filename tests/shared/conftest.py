import os
import sys
from pathlib import Path

os.environ["JWT_SECRET"] = "test-jwt-secret-for-shared-tests-0123456789"
os.environ["HMAC_WEBHOOK_SECRET"] = "test-hmac-secret-for-shared-tests-0123456789"

SERVICES_DIR = Path(__file__).resolve().parents[2] / "services"
sys.path.insert(0, str(SERVICES_DIR))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import DeclarativeBase, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


@pytest.fixture
def make_base():
    def _make() -> type:
        class Base(DeclarativeBase):
            pass

        return Base

    return _make


@pytest.fixture
def make_session_factory():
    def _make(Base: type):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    return _make

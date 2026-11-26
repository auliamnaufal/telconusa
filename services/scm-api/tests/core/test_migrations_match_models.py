import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.database import Base

API_DIR = Path(__file__).resolve().parents[2]


def alembic_config(url: str) -> Config:
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "alembic"))
    os.environ["DATABASE_URL"] = url
    return config


def upgrade(tmp_path, monkeypatch) -> str:
    url = f"sqlite:///{tmp_path / 'scm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(alembic_config(url), "heads")
    return url


def test_upgrade_heads_creates_exactly_the_model_tables_and_columns(tmp_path, monkeypatch):
    url = upgrade(tmp_path, monkeypatch)
    inspector = inspect(create_engine(url))

    migrated = {name for name in inspector.get_table_names() if name != "alembic_version"}
    assert migrated == set(Base.metadata.tables)
    for name, table in Base.metadata.tables.items():
        assert {c["name"] for c in inspector.get_columns(name)} == {c.name for c in table.columns}, name


def test_upgrade_heads_twice_is_a_no_op_and_every_slice_has_its_own_head(tmp_path, monkeypatch):
    url = upgrade(tmp_path, monkeypatch)
    command.upgrade(alembic_config(url), "heads")

    with create_engine(url).connect() as connection:
        revisions = {row[0] for row in connection.exec_driver_sql("select version_num from alembic_version")}
    # `core_0001` adalah leluhur keempat head slice (depends_on), jadi tidak tercatat sebagai head.
    assert revisions == {"stock_0001", "procurement_0001", "assets_0001", "catalog_0001"}


def test_downgrade_to_base_removes_every_table(tmp_path, monkeypatch):
    url = upgrade(tmp_path, monkeypatch)
    command.downgrade(alembic_config(url), "base")
    remaining = {name for name in inspect(create_engine(url)).get_table_names() if name != "alembic_version"}
    assert remaining == set()

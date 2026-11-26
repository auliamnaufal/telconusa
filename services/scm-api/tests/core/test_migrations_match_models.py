import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
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


def test_upgrade_heads_twice_is_a_no_op_and_every_slice_has_exactly_one_head(tmp_path, monkeypatch):
    url = upgrade(tmp_path, monkeypatch)
    config = alembic_config(url)
    command.upgrade(config, "heads")

    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    labels = set().union(*(script.get_revision(head).branch_labels for head in heads))
    slice_heads = {head for head in heads if head != "core_0001"}
    # `core` tetap berstatus head di skrip (depends_on tidak membuatnya leluhur), tetapi tidak tercatat di
    # alembic_version karena sudah dipenuhi oleh keempat slice. Tiap slice harus punya tepat satu head.
    assert labels - {"core"} == {"stock", "procurement", "assets", "catalog"}
    assert len(slice_heads) == 4
    with create_engine(url).connect() as connection:
        revisions = {row[0] for row in connection.exec_driver_sql("select version_num from alembic_version")}
    assert revisions == slice_heads


def test_lot_migration_turns_existing_non_serial_balances_into_one_opening_lot(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'scm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = alembic_config(url)
    command.upgrade(config, "stock_0001")

    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql("INSERT INTO warehouses (code, name, city_code) VALUES ('WH-BDG', 'Bandung', 'BDG')")
        connection.exec_driver_sql(
            "INSERT INTO items (sku, name, unit, unit_cost, reorder_point, safety_stock, is_serialized) VALUES "
            "('CBL-FO', 'Kabel', 'METER', 4000, 10, 5, 0), ('ONT-01', 'ONT', 'UNIT', 350000, 10, 5, 1)"
        )
        connection.exec_driver_sql(
            "INSERT INTO inventory_balances (id, warehouse_code, item_sku, qty_physical, qty_reserved, qty_damaged, version) VALUES "
            "('b1', 'WH-BDG', 'CBL-FO', 100, 0, 10, 1), ('b2', 'WH-BDG', 'ONT-01', 20, 0, 0, 1)"
        )

    command.upgrade(config, "stock_0002")

    with engine.connect() as connection:
        lots = connection.exec_driver_sql("SELECT item_sku, qty_remaining, seq, ref_no FROM stock_lots").fetchall()
        counter = connection.exec_driver_sql("SELECT value FROM id_counters WHERE key = 'LOT'").scalar()
    assert lots == [("CBL-FO", 90, 1, "MIGRATION")], "stok baik non-serial saja; ONT serial tidak punya lot"
    assert counter == 1


def test_downgrade_to_base_removes_every_table(tmp_path, monkeypatch):
    url = upgrade(tmp_path, monkeypatch)
    command.downgrade(alembic_config(url), "base")
    remaining = {name for name in inspect(create_engine(url)).get_table_names() if name != "alembic_version"}
    assert remaining == set()

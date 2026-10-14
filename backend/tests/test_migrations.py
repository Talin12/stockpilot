from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.db import Base

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    config.attributes["configure_logger"] = False
    return config


def test_migrations_upgrade_and_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrations.db'}"
    config = alembic_config(url)

    engine = create_engine(url)
    try:
        command.upgrade(config, "head")
        assert {"products", "stock_movements", "alembic_version"} <= set(inspect(engine).get_table_names())

        command.downgrade(config, "base")
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()


def test_migrations_match_models(tmp_path):
    """Fails if someone changes a model without writing a migration."""
    url = f"sqlite:///{tmp_path / 'drift.db'}"
    command.upgrade(alembic_config(url), "head")
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()
    assert diff == []

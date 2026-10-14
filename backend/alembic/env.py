from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import settings
from app.db import Base

config = context.config
if config.config_file_name and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
# Tests pass an explicit URL; containers use DATABASE_URL from the environment.
database_url = config.get_main_option("sqlalchemy.url") or settings.database_url

# Arbitrary constant: every backend replica runs migrations on start-up, and this
# PostgreSQL advisory lock makes them take turns instead of racing each other.
MIGRATION_LOCK_ID = 7_201_042


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        is_postgres = connection.dialect.name == "postgresql"
        if is_postgres:
            connection.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            connection.commit()
        try:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
            connection.commit()
        finally:
            if is_postgres:
                connection.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

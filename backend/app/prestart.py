"""Container entrypoint step: wait for PostgreSQL, apply migrations, optionally seed.

Run as `python -m app.prestart` before Uvicorn starts.
"""

import logging
import sys
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .config import settings
from .db import SessionLocal, engine
from .seed import seed_demo_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("stockpilot.prestart")

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def wait_for_database(attempts: int = 30, delay: float = 2.0) -> None:
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("database is reachable")
            return
        except OperationalError as exc:
            logger.warning("database not ready (%d/%d): %s", attempt, attempts, exc.orig)
            time.sleep(delay)
    logger.error("database never became reachable, giving up")
    sys.exit(1)


def main() -> None:
    wait_for_database()
    logger.info("running alembic migrations")
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_data(db)


if __name__ == "__main__":
    main()

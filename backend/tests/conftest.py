import os

# Point the app at SQLite before it is imported, so no test can ever reach PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_DEMO_DATA"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """A brand-new in-memory database for every test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_product(client):
    def _make(**overrides):
        payload = {
            "sku": "TEST-001",
            "name": "Test Widget",
            "category": "Testing",
            "quantity": 20,
            "reorder_level": 5,
            "unit_price": 99.5,
            "supplier": "Acme",
            "location": "A1",
        }
        payload.update(overrides)
        response = client.post("/api/products", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make

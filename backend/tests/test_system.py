from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app


def test_root_describes_service(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "StockPilot API"


def test_health_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_when_database_reachable(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_ready_returns_503_when_database_down(client):
    class BrokenSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    response = client.get("/ready")
    assert response.status_code == 503


def test_info_exposes_build_metadata(client):
    body = client.get("/api/info").json()
    assert set(body) == {"service", "version", "environment", "git_sha"}


def test_metrics_endpoint_is_prometheus_format(client):
    client.get("/api/products")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "stockpilot_products_created_total" in response.text

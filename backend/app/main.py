import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import __version__
from .config import settings
from .db import get_db
from .routers import inventory, products
from .schemas import InfoOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("stockpilot")

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Inventory management API: products, stock movements and stock analytics.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP request count/latency/in-progress metrics, served at /metrics for Prometheus.
Instrumentator(
    excluded_handlers=["/metrics", "/health", "/ready"],
    should_instrument_requests_inprogress=True,
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(products.router)
app.include_router(inventory.router)


@app.get("/", tags=["system"])
def root():
    return {"service": settings.app_name, "version": __version__, "docs": "/docs"}


@app.get("/health", tags=["system"])
def health():
    """Liveness: the process is up. Deliberately does not touch the database."""
    return {"status": "UP"}


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only accept traffic when the database answers."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "READY"}


@app.get("/api/info", response_model=InfoOut, tags=["system"])
def info():
    return InfoOut(
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
        git_sha=settings.git_sha,
    )

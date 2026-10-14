# syntax=docker/dockerfile:1

# ---- build stage: resolve dependencies into an isolated virtualenv ----
FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt \
    # pip is only needed to build the venv. It vendors its own urllib3/msgpack/setuptools
    # copies, which Trivy flags, so it is removed before the venv is copied to runtime.
    && pip uninstall -y pip

# ---- runtime stage: no compilers, no pip cache, non-root ----
FROM python:3.13-slim AS runtime
LABEL org.opencontainers.image.title="stockpilot-backend" \
      org.opencontainers.image.description="StockPilot inventory API (FastAPI)" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Pull in Debian security fixes released after the base image was built,
# and drop pip/setuptools from the system interpreter (the app uses the venv).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip setuptools 2>/dev/null || true \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=10001:10001 alembic.ini ./
COPY --chown=10001:10001 alembic ./alembic
COPY --chown=10001:10001 app ./app
COPY --chown=10001:10001 docker-entrypoint.sh ./

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]

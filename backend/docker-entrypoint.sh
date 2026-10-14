#!/bin/sh
set -e

# 1. wait for PostgreSQL  2. alembic upgrade head  3. optional demo seed
python -m app.prestart

# exec so Uvicorn becomes PID 1 and receives SIGTERM from Docker/Kubernetes directly.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips "*" \
  --no-access-log

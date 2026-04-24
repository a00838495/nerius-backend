#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Nerius API on port ${PORT:-8080}..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --workers 1

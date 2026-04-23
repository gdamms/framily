#!/bin/sh
set -eu

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Gunicorn server..."
exec uv run gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${BACKEND_WORKERS:-2}" \
    --bind 0.0.0.0:8000

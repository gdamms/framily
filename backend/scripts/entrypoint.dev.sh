#!/bin/sh
set -eu

echo "Syncing dependencies with uv..."
uv sync --frozen

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Uvicorn server..."
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

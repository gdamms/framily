#!/bin/bash
set -e

DEV_ENV_DIR=".venv"

echo "Installing dependencies..."
if [ ! -d "${DEV_ENV_DIR}" ]; then
    python -m venv ${DEV_ENV_DIR}
fi
source ${DEV_ENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload

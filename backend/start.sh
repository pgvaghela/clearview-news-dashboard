#!/bin/bash
set -e
echo "=== Running migrations ==="
alembic upgrade head
echo "=== Migrations complete ==="
echo "=== Starting uvicorn on port $PORT ==="
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT

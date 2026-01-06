#!/bin/bash
set -e

# Ensure current directory is in PYTHONPATH
export PYTHONPATH=$PYTHONPATH:/app

# Wait for the database to be ready
echo "Waiting for the database to be ready..."
python /app/app/check_db_ready.py

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Run the seeding script only if RUN_SEEDS is true
if [ "$RUN_SEEDS" = "True" ] || [ "$RUN_SEEDS" = "true" ]; then
    echo "Seeding the database..."
    python -m app.seed
else
    echo "Skipping database seeding (RUN_SEEDS is not true)"
fi

# Start the Uvicorn server
echo "Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000

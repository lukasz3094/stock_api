#!/bin/bash

# Wait for the database to be ready
echo "Waiting for the database to be ready..."
python /app/app/check_db_ready.py
if [ $? -ne 0 ]; then
    echo "Database did not become ready. Exiting."
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Run the seeding script
echo "Seeding the database..."
python -m app.seed

# Start the Uvicorn server
echo "Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000

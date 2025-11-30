import os
import time
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
  print("DATABASE_URL environment variable not set.")
  exit(1)

# Replace the asyncpg dialect with psycopg2 compatible one
DB_URL_PSYCOPG2 = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

max_attempts = 10
attempt = 0
while attempt < max_attempts:
  try:
    conn = psycopg2.connect(DB_URL_PSYCOPG2)
    conn.close()
    print("Database is ready!")
    exit(0)
  except psycopg2.OperationalError as e:
    print(f"Database not ready yet. Retrying in 5 seconds... ({e})")
    attempt += 1
    time.sleep(5)
  except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

print("Failed to connect to the database after multiple attempts.")
exit(1)

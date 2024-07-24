#!/usr/bin/env bash
function check_db {
    python - <<END
import psycopg2
import sys
import os
try:
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'), 
        user=os.getenv('POSTGRES_USER'), 
        password=os.getenv('POSTGRES_PASSWORD'), 
        host=os.getenv('POSTGRES_HOST')
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
}

# Loop until the database is ready
until check_db; do
    echo "Waiting for the database to be ready..."
    sleep 2
done

# Start app
python init_db.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
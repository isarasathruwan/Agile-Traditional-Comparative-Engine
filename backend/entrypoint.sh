#!/bin/sh
set -e

echo "Waiting for database at $POSTGRES_HOST:$POSTGRES_PORT..."

# Quick DNS check
echo "Checking DNS resolution for '$POSTGRES_HOST'..."
if command -v getent >/dev/null 2>&1; then
    getent hosts "$POSTGRES_HOST" || echo "WARNING: Could not resolve '$POSTGRES_HOST' via getent"
elif command -v nslookup >/dev/null 2>&1; then
    nslookup "$POSTGRES_HOST" 2>/dev/null || echo "WARNING: Could not resolve '$POSTGRES_HOST' via nslookup"
else
    echo "No DNS lookup tools available in container"
fi

max_retries=30
retry_count=0

while ! python -c "
import sys
import psycopg
try:
    psycopg.connect(
        host='$POSTGRES_HOST',
        port='$POSTGRES_PORT',
        user='$POSTGRES_USER',
        password='$POSTGRES_PASSWORD',
        dbname='$POSTGRES_DB'
    )
    sys.exit(0)
except Exception as e:
    print(f'Connection failed: {e}', file=sys.stderr)
    sys.exit(1)
"; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "Database is not available after $max_retries retries. Exiting."
        exit 1
    fi
    echo "Database not ready yet. Retrying in 2s... ($retry_count/$max_retries)"
    sleep 2
done

echo "Database is ready. Running migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000

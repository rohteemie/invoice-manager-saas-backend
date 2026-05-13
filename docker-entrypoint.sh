#!/bin/bash
# Docker entrypoint script for Multi-Tenant SaaS Backend
# This script runs database migrations when starting the API

set -e  # Exit on error
set -u  # Exit on undefined variable

echo "🚀 Starting Multi-Tenant SaaS Backend..."

run_migrations=true
if [ "$#" -gt 0 ]; then
    if [ "$1" = "celery" ]; then
        run_migrations=false
    elif [ "$1" != "uvicorn" ]; then
        run_migrations=false
    fi
fi

if [ "$run_migrations" = "true" ]; then
    # Run Alembic migrations
    echo "📋 Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations completed successfully"
fi

if [ "$#" -gt 0 ]; then
    if [ "$run_migrations" = "false" ]; then
        echo "⚙️ Running custom command: $*"
    else
        echo "🌐 Starting API command: $*"
    fi
    exec "$@"
fi

# Start the FastAPI application
echo "🌐 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

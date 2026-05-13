#!/bin/bash
# Docker entrypoint script for Multi-Tenant SaaS Backend
# This script runs database migrations when starting the API

set -e  # Exit on error
set -u  # Exit on undefined variable

echo "🚀 Starting Multi-Tenant SaaS Backend..."

run_migrations=false
# Run migrations only for API server commands (uvicorn directly or via python -m)
if [ "$#" -eq 0 ]; then
    run_migrations=true
else
    case "$1" in
        uvicorn)
            run_migrations=true
            ;;
        celery)
            run_migrations=false
            ;;
        python|python3)
            prev=""
            for arg in "$@"; do
                if [ "$prev" = "-m" ] && [ "$arg" = "uvicorn" ]; then
                    run_migrations=true
                    break
                fi
                prev="$arg"
            done
            ;;
    esac
fi

if [ "$run_migrations" = "true" ]; then
    # Run Alembic migrations
    echo "📋 Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Migrations completed successfully"
fi

if [ "$#" -gt 0 ]; then
    echo "⚙️ Running command: $*"
    exec "$@"
fi

# Start the FastAPI application
echo "🌐 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

#!/bin/bash
# Docker entrypoint script for Multi-Tenant SaaS Backend
# This script runs database migrations before starting the application

set -e  # Exit on error
set -u  # Exit on undefined variable

echo "🚀 Starting Multi-Tenant SaaS Backend..."

# Run Alembic migrations
echo "📋 Running Alembic migrations..."
alembic upgrade head
echo "✅ Migrations completed successfully"

# Start the FastAPI application
echo "🌐 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

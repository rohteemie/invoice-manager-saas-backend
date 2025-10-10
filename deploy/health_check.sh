#!/usr/bin/env bash

# Health check script for the application
# Can be used for monitoring and load balancer health checks

APP_URL="http://localhost:8000"
SERVICE_NAME="multi-tenant-saas"

# Optional flags
SHOW_STATUS=false
SHOW_LOGS=false
FOLLOW_LOGS=false

# Parse flags (supports multiple flags)
for arg in "$@"; do
    case "$arg" in
        --show-status|-s)
            SHOW_STATUS=true
            ;;
        --logs|-l)
            SHOW_LOGS=true
            ;;
        --follow-logs|-f)
            SHOW_LOGS=true
            FOLLOW_LOGS=true
            ;;
    esac
done

# Check if the application is responding
check_app_health() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)
    if [ "$response" = "200" ]; then
        echo "✅ Application is healthy (HTTP $response)"
        return 0
    else
        echo "❌ Application is unhealthy (HTTP $response)"
        return 1
    fi
}

# Check if the service is running
check_service_status() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Service $SERVICE_NAME is running"
        return 0
    else
        echo "❌ Service $SERVICE_NAME is not running"
        return 1
    fi
}

# Show detailed service status (no pager)
show_service_status() {
    echo "\nℹ️  Detailed service status (systemctl):"
    systemctl status "$SERVICE_NAME" --no-pager || true
}

# Show service logs
show_service_logs() {
    echo ""
    if [ "$FOLLOW_LOGS" = true ]; then
        echo "📜 Following logs for $SERVICE_NAME (Ctrl+C to stop)..."
        journalctl -u "$SERVICE_NAME" -f || true
    else
        echo "📜 Recent logs for $SERVICE_NAME (last 200 lines):"
        journalctl -u "$SERVICE_NAME" -n 200 --no-pager || true
    fi
}

# Main health check
main() {
    echo "🔍 Performing health check..."

    local exit_code=0

    if ! check_service_status; then
        exit_code=1
    fi

    if ! check_app_health; then
        exit_code=1
    fi

    if [ $exit_code -eq 0 ]; then
        echo "🎉 All health checks passed!"
    else
        echo "⚠️  Health check failed!"
    fi

    # Optionally show detailed service status
    if [ "$SHOW_STATUS" = true ]; then
        show_service_status
    fi

    if [ "$SHOW_LOGS" = true ]; then
        show_service_logs
    fi

    exit $exit_code
}

main "$@"
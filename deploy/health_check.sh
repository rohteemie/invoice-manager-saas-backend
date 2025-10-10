#!/usr/bin/env bash

# Health check script for the application
# Can be used for monitoring and load balancer health checks

APP_URL="http://localhost:8000"
SERVICE_NAME="multi-tenant-saas"

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
    
    exit $exit_code
}

main "$@"
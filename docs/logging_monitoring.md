# Logging & Monitoring Documentation

## Overview

The Multi-Tenant SaaS Backend implements comprehensive logging and monitoring to ensure observability, error tracking, and performance analysis in production environments.

## Architecture

### Components

1. **Structured Logging**: Request/response logging with context
2. **Error Monitoring**: Sentry integration for error tracking
3. **Metrics Collection**: Prometheus metrics for performance monitoring
4. **Health Checks**: Service health endpoints for load balancers

## Structured Logging

### Implementation

**Location**: `app/core/logging.py`

The logging system captures:
- All HTTP requests and responses
- Request duration
- Client information (IP, User-Agent)
- Error traces with full context

### Log Format

```json
{
  "timestamp": "2024-10-08T17:45:49.438",
  "level": "INFO",
  "message": "Response: 200 (0.042s) GET /api/v1/invoices/",
  "method": "GET",
  "url": "/api/v1/invoices/",
  "client_host": "127.0.0.1",
  "status_code": 200,
  "duration": "0.042s"
}
```

### Middleware

The `LoggingMiddleware` automatically logs all requests:

```python
from app.core.logging import LoggingMiddleware

app.add_middleware(LoggingMiddleware)
```

### Features

- **Automatic Request Logging**: Every HTTP request is logged
- **Duration Tracking**: Response times are measured
- **Error Context**: Errors include full stack traces
- **Sensitive Data Filtering**: Passwords and tokens are excluded

### Usage

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Processing invoice", extra={"invoice_id": invoice.id})
logger.error("Failed to process", exc_info=True)
```

## Error Monitoring (Sentry)

### Setup

**Location**: `app/core/sentry.py`

Sentry provides real-time error tracking and performance monitoring.

### Configuration

Add to `.env`:

```bash
SENTRY_DSN=https://<key>@<project>.ingest.sentry.io/<id>
ENVIRONMENT=production
```

### Features

1. **Error Tracking**: Automatic capture of exceptions
2. **Performance Monitoring**: Transaction tracing
3. **Release Tracking**: Version-based error monitoring
4. **User Context**: User information with errors
5. **Filtered Transactions**: Health checks excluded

### Initialization

```python
from app.core.sentry import init_sentry

init_sentry()  # Called at app startup
```

### Error Filtering

Health checks and metrics endpoints are filtered:

```python
def filter_transactions(event, hint):
    if event.get("request", {}).get("url", "").endswith(("/health", "/metrics")):
        return None
    return event
```

### Sample Rates

- **Development**: 100% trace and profile sampling
- **Production**: 10% sampling (configurable)

## Prometheus Metrics

### Endpoints

**Metrics URL**: `GET /metrics`

Exposes Prometheus-compatible metrics in text format.

### Available Metrics

#### HTTP Metrics

```prometheus
# Total HTTP requests by method, endpoint, and status
http_requests_total{method="GET",endpoint="/api/v1/invoices",status="200"} 150

# Request duration histogram
http_request_duration_seconds{method="GET",endpoint="/api/v1/invoices"} 0.042

# Requests in progress
http_requests_in_progress{method="POST",endpoint="/api/v1/auth/login"} 3
```

#### Business Metrics

```prometheus
# Total invoices created
invoices_total{tenant_id="123",status="paid"} 45

# Invoice amounts
invoice_amount_total{tenant_id="123",currency="USD"} 150000.00
```

### Integration

Add to your monitoring stack:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'multi-tenant-saas'
    static_configs:
      - targets: ['api.example.com:8000']
    metrics_path: '/metrics'
```

### Custom Metrics

```python
from app.core.metrics import invoices_total, invoice_amount_total

# Increment invoice counter
invoices_total.labels(
    tenant_id=invoice.tenant_id,
    status=invoice.status
).inc()

# Add to amount counter
invoice_amount_total.labels(
    tenant_id=invoice.tenant_id,
    currency=invoice.currency
).inc(invoice.total_amount)
```

## Health Checks

### Endpoint

**URL**: `GET /health`

**Response**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

### Usage

- **Load Balancers**: Configure health check endpoint
- **Kubernetes**: Use as liveness/readiness probe
- **Monitoring**: Alert on non-200 responses

### Kubernetes Example

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1
```

## Configuration

### Environment Variables

```bash
# Sentry Configuration
SENTRY_DSN=https://<key>@sentry.io/<project>
ENVIRONMENT=production  # development, staging, production

# Logging Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Metrics Configuration
METRICS_ENABLED=true
```

### Disable Monitoring

To disable specific components:

```python
# Disable Sentry (don't set SENTRY_DSN)
SENTRY_DSN=

# Disable metrics
METRICS_ENABLED=false
```

## Grafana Dashboard

### Sample Queries

**Request Rate**:
```promql
rate(http_requests_total[5m])
```

**Error Rate**:
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**Request Duration (p95)**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Invoice Creation Rate**:
```promql
rate(invoices_total[1h])
```

## Alerting

### Sample Alerts

#### High Error Rate

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} errors/sec"
```

#### Slow Responses

```yaml
- alert: SlowResponses
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 10m
  annotations:
    summary: "Slow API responses"
    description: "95th percentile response time is {{ $value }}s"
```

## Best Practices

### Logging

1. **Use Appropriate Levels**:
   - DEBUG: Detailed debug information
   - INFO: General informational messages
   - WARNING: Warning messages
   - ERROR: Error messages with context

2. **Add Context**: Include relevant data in log messages

3. **Avoid Sensitive Data**: Never log passwords, tokens, or PII

4. **Use Structured Logging**: Include extra fields for filtering

### Monitoring

1. **Set Meaningful Alerts**: Alert on actionable metrics
2. **Use Percentiles**: p95, p99 for latency monitoring
3. **Monitor Business Metrics**: Track invoices, revenue, users
4. **Set Baselines**: Know your normal operating ranges

### Error Tracking

1. **Group Similar Errors**: Use Sentry's grouping
2. **Add User Context**: Include user ID for debugging
3. **Set Release Tags**: Track errors by version
4. **Monitor Error Trends**: Watch for increasing error rates

## Troubleshooting

### No Logs Appearing

- Check log level configuration
- Verify middleware is added to app
- Check file permissions for log files

### Sentry Not Receiving Errors

- Verify SENTRY_DSN is set correctly
- Check network connectivity to Sentry
- Verify environment is configured

### Metrics Not Available

- Check `/metrics` endpoint accessibility
- Verify Prometheus can scrape the endpoint
- Check firewall rules

## Performance Impact

- **Logging**: < 1ms overhead per request
- **Sentry**: < 5ms with sampling enabled
- **Metrics**: < 0.5ms per request
- **Total Overhead**: < 10ms per request

## Security Considerations

1. **Sensitive Data**: Logs exclude passwords, tokens
2. **PII Protection**: User data is anonymized in Sentry
3. **Access Control**: Metrics endpoint should be protected in production
4. **Data Retention**: Configure appropriate retention periods

## Integration Examples

### Docker Compose

```yaml
services:
  app:
    environment:
      - SENTRY_DSN=${SENTRY_DSN}
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
  
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-tenant-saas
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"
    prometheus.io/port: "8000"
```

---

**Last Updated**: Phase 4 - Sprint 4.3  
**Version**: 1.0.0  
**Status**: ✅ Active

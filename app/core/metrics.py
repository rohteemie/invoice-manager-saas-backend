"""
Prometheus metrics configuration.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Business metrics
invoices_total = Counter(
    'invoices_total',
    'Total invoices created',
    ['tenant_id', 'status']
)

invoice_amount_total = Counter(
    'invoice_amount_total',
    'Total invoice amount',
    ['tenant_id', 'currency']
)


def metrics_endpoint():
    """Endpoint to expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

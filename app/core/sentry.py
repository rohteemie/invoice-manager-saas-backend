"""
Sentry integration for error monitoring.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings


def init_sentry():
    """Initialize Sentry SDK for error monitoring."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=1.0 if settings.ENVIRONMENT == "development"
            else 0.1,
            profiles_sample_rate=1.0 if settings.ENVIRONMENT == "development"
            else 0.1,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            # Don't send sensitive data
            send_default_pii=False,
            # Filter out health checks and metrics
            before_send=filter_transactions,
        )
        print(f"✅ Sentry initialized for environment: {settings.ENVIRONMENT}")
    else:
        print("⚠️  Sentry DSN not configured. Error monitoring disabled.")


def filter_transactions(event, hint):
    """Filter out health checks and metrics from Sentry."""
    # Don't send health check or metrics requests
    if event.get("request", {}).get("url", "").endswith(("/health", "/metrics")):
        return None
    return event

"""
Celery configuration for background tasks.
"""
from celery import Celery
from app.core.config import settings

# Initialize Celery app
# Use Redis as both broker and result backend
# If Redis URL is not configured, use a fallback
broker_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
result_backend = broker_url

celery_app = Celery(
    'multi_tenant_saas',
    broker=broker_url,
    backend=result_backend,
    include=['app.tasks.invoice_tasks', 'app.tasks.email_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Periodic task schedule (if using celery beat)
celery_app.conf.beat_schedule = {
    'check-overdue-invoices': {
        'task': 'app.tasks.invoice_tasks.check_overdue_invoices',
        'schedule': 3600.0,  # Run every hour
    },
    'send-verification-reminders': {
        'task': 'app.tasks.email_tasks.send_verification_reminders',
        'schedule': 86400.0,  # Run once daily (24 hours)
    },
}

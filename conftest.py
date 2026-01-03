import os
import pytest
from unittest.mock import MagicMock

# Set TESTING environment variable before any app imports
os.environ["TESTING"] = "1"
# Set required environment variables for tests
os.environ["PROJECT_NAME"] = "Multi-Tenant SaaS Backend Test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["EMAIL_PROVIDER"] = "mock"


# Mock Celery tasks at module level before importing
import sys
from unittest.mock import MagicMock

# Create mock email tasks module
email_tasks_mock = MagicMock()
sys.modules['app.tasks.email_tasks'] = email_tasks_mock

# Create individual task mocks with delay method
send_verification_email_task = MagicMock()
send_verification_email_task.delay = MagicMock(
    return_value=MagicMock(id='verify-task-id')
)
email_tasks_mock.send_verification_email_task = send_verification_email_task

send_password_reset_email_task = MagicMock()
send_password_reset_email_task.delay = MagicMock(
    return_value=MagicMock(id='reset-task-id')
)
email_tasks_mock.send_password_reset_email_task = send_password_reset_email_task

send_invoice_email_task = MagicMock()
send_invoice_email_task.delay = MagicMock(
    return_value=MagicMock(id='invoice-task-id')
)
email_tasks_mock.send_invoice_email_task = send_invoice_email_task

send_verification_reminder_task = MagicMock()
send_verification_reminder_task.delay = MagicMock(
    return_value=MagicMock(id='reminder-task-id')
)
email_tasks_mock.send_verification_reminder_task = send_verification_reminder_task



"""
Background tasks for email processing with retry logic.

This module provides Celery tasks for sending emails asynchronously
with exponential backoff for transient failures.
"""
from datetime import datetime, timezone
import logging
import base64
from typing import Optional

from app.core.celery_app import celery_app
from app.services.email_service import (
    get_configured_email_provider,
    compose_verification_email,
    compose_password_reset_email,
    compose_verification_reminder_email,
    compose_invoice_email,
    sanitize_filename,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name='app.tasks.email_tasks.send_verification_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute initial delay
)
def send_verification_email_task(
    self,
    email: str,
    token: str,
    full_name: str,
    base_url: str,
) -> dict:
    """
    Send verification email asynchronously with retry logic.

    Args:
        self: Celery task instance (for retry)
        email: Recipient email address
        token: Verification token
        full_name: Recipient's full name
        base_url: Base URL for verification link

    Returns:
        dict: Result status
    """
    try:
        # Get email provider
        provider = get_configured_email_provider()
        if not provider:
            logger.error(
                "Email provider not configured for verification email to %s",
                email
            )
            return {
                "status": "error",
                "message": "Email provider not configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Build verification link
        verification_link = f"{base_url.rstrip('/')}/verify-email?token={token}"

        # Compose email content
        plain_text, html_content = compose_verification_email(
            full_name, verification_link
        )

        # Send email
        success = provider.send_email(
            to_email=email,
            subject="Verify your email address",
            plain_text=plain_text,
            html_content=html_content,
        )

        if success:
            return {
                "status": "success",
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Retry with exponential backoff
            retry_delay = 60 * (2 ** self.request.retries)  # Exponential backoff
            raise self.retry(countdown=retry_delay, exc=Exception(
                "Failed to send verification email"
            ))

    except Exception as exc:
        logger.error(
            "Error sending verification email to %s: %s",
            email, str(exc), exc_info=True
        )

        # Retry with exponential backoff if not max retries
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=exc)

        return {
            "status": "error",
            "message": str(exc),
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(
    name='app.tasks.email_tasks.send_password_reset_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_password_reset_email_task(
    self,
    email: str,
    token: str,
    full_name: str,
    base_url: str,
) -> dict:
    """
    Send password reset email asynchronously with retry logic.

    Args:
        self: Celery task instance (for retry)
        email: Recipient email address
        token: Password reset token
        full_name: Recipient's full name
        base_url: Base URL for reset link

    Returns:
        dict: Result status
    """
    try:
        provider = get_configured_email_provider()
        if not provider:
            logger.error(
                "Email provider not configured for password reset email to %s",
                email
            )
            return {
                "status": "error",
                "message": "Email provider not configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Build reset link
        reset_link = f"{base_url.rstrip('/')}/reset-password?token={token}"

        # Compose email content
        plain_text, html_content = compose_password_reset_email(
            full_name, reset_link
        )

        # Send email
        success = provider.send_email(
            to_email=email,
            subject="Password Reset Request",
            plain_text=plain_text,
            html_content=html_content,
        )

        if success:
            return {
                "status": "success",
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=Exception(
                "Failed to send password reset email"
            ))

    except Exception as exc:
        logger.error(
            "Error sending password reset email to %s: %s",
            email, str(exc), exc_info=True
        )

        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=exc)

        return {
            "status": "error",
            "message": str(exc),
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(
    name='app.tasks.email_tasks.send_verification_reminder_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_verification_reminder_task(
    self,
    email: str,
    token: str,
    full_name: str,
    base_url: str,
) -> dict:
    """
    Send verification reminder email asynchronously with retry logic.

    Args:
        self: Celery task instance (for retry)
        email: Recipient email address
        token: Verification token
        full_name: Recipient's full name
        base_url: Base URL for verification link

    Returns:
        dict: Result status
    """
    try:
        provider = get_configured_email_provider()
        if not provider:
            logger.error(
                "Email provider not configured for reminder email to %s",
                email
            )
            return {
                "status": "error",
                "message": "Email provider not configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Build verification link
        verification_link = f"{base_url.rstrip('/')}/verify-email?token={token}"

        # Compose email content
        plain_text, html_content = compose_verification_reminder_email(
            full_name, verification_link
        )

        # Send email
        success = provider.send_email(
            to_email=email,
            subject="Reminder: Verify your email address",
            plain_text=plain_text,
            html_content=html_content,
        )

        if success:
            return {
                "status": "success",
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=Exception(
                "Failed to send reminder email"
            ))

    except Exception as exc:
        logger.error(
            "Error sending reminder email to %s: %s",
            email, str(exc), exc_info=True
        )

        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=exc)

        return {
            "status": "error",
            "message": str(exc),
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(
    name='app.tasks.email_tasks.send_invoice_email_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_invoice_email_task(
    self,
    email: str,
    customer_name: str,
    invoice_number: str,
    pdf_bytes_b64: str,
    total_amount: str,
) -> dict:
    """
    Send invoice email with PDF attachment asynchronously with retry logic.

    Args:
        self: Celery task instance (for retry)
        email: Customer email address
        customer_name: Customer's name
        invoice_number: Invoice number
        pdf_bytes_b64: Base64 encoded PDF content
        total_amount: Formatted total amount

    Returns:
        dict: Result status
    """
    try:
        provider = get_configured_email_provider()
        if not provider:
            logger.error(
                "Email provider not configured for invoice email to %s",
                email
            )
            return {
                "status": "error",
                "message": "Email provider not configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Compose email content
        plain_text, html_content = compose_invoice_email(
            customer_name, invoice_number, total_amount
        )

        # Prepare attachment
        from app.core.config import settings
        from app.services.email_service import sanitize_for_email

        safe_invoice_number = sanitize_for_email(invoice_number)
        safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

        attachments = [
            {
                "content": pdf_bytes_b64,  # Already base64 encoded
                "type": "application/pdf",
                "filename": sanitize_filename(f"invoice_{invoice_number}.pdf"),
                "disposition": "attachment"
            }
        ]

        # Send email
        success = provider.send_email(
            to_email=email,
            subject=f"Invoice {safe_invoice_number} from {safe_project_name}",
            plain_text=plain_text,
            html_content=html_content,
            attachments=attachments,
        )

        if success:
            return {
                "status": "success",
                "email": email,
                "invoice_number": invoice_number,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=Exception(
                "Failed to send invoice email"
            ))

    except Exception as exc:
        logger.error(
            "Error sending invoice email to %s: %s",
            email, str(exc), exc_info=True
        )

        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay, exc=exc)

        return {
            "status": "error",
            "message": str(exc),
            "email": email,
            "invoice_number": invoice_number,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@celery_app.task(
    name='app.tasks.email_tasks.send_verification_reminders'
)
def send_verification_reminders():
    """
    Background task to send verification reminders to unverified users.

    This task runs periodically (daily by default) and:
    1. Finds all unverified users registered more than 24 hours ago
    2. Sends reminder emails to those who haven't verified
    3. Only sends one reminder per user per day

    Returns:
        dict: Summary of processed reminders
    """
    from datetime import timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.user import User as UserModel

    # Create database engine for tasks
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        # Find unverified users registered more than 24 hours ago
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        unverified_users = db.query(UserModel).filter(
            UserModel.is_verified == False,  # noqa: E712
            UserModel.is_active == True,  # noqa: E712
            UserModel.verification_token.isnot(None),
            UserModel.verification_token_expires_at.isnot(None),
            UserModel.verification_token_expires_at > datetime.now(timezone.utc),
            UserModel.created_at < cutoff_time,
        ).all()

        sent_count = 0
        failed_count = 0

        base_url = settings.EMAIL_VERIFICATION_BASE_URL or "http://localhost:5173"

        for user in unverified_users:
            try:
                # Send reminder email asynchronously
                send_verification_reminder_task.delay(
                    email=user.email,
                    token=user.verification_token,
                    full_name=user.full_name,
                    base_url=base_url,
                )
                sent_count += 1
            except Exception as e:
                logger.error(
                    "Failed to queue reminder for %s: %s",
                    user.email, str(e)
                )
                failed_count += 1

        return {
            "status": "success",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_unverified": len(unverified_users),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(
            "Error in send_verification_reminders: %s",
            str(e), exc_info=True
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()

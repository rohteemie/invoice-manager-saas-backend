"""
Email service for sending verification and notification emails.
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(
    email: str,
    token: str,
    full_name: str,
    base_url: Optional[str] = None,
) -> bool:
    """
    Send a verification email using SendGrid's Web API v3.

    This implementation uses `httpx` to avoid adding a heavy SDK dependency.
    It reads the SendGrid API key and sender address from `settings` so secrets
    are loaded from environment variables and not committed to source.

    Security / best-practices applied:
    - API key is read from environment and not logged.
    - Errors from the email provider are logged at WARNING level without
      exposing sensitive headers or the API key.
    - The function returns a boolean success indicator; in production this
      should be executed in a background task or a worker to avoid slowing
      request handling.

    Args:
        email: Recipient email address
        token: Verification token
        full_name: Recipient full name
        base_url: Optional base URL to build verification link; falls back to
            settings.EMAIL_VERIFICATION_BASE_URL

    Returns:
        True if send request was accepted by SendGrid, False otherwise.
    """
    sg_api_key = settings.SENDGRID_API_KEY
    sender = settings.EMAILS_FROM

    if not sg_api_key or not sender:
        logger.warning(
            "SendGrid not configured "
            "(missing SENDGRID_API_KEY or EMAILS_FROM). Email not sent."
        )
        return False

    if base_url is None:
        base_url = (
            settings.EMAIL_VERIFICATION_BASE_URL or "http://localhost:5173"
        )

    verification_link = f"{base_url.rstrip('/')}/verify-email?token={token}"

    payload = {
        "personalizations": [
            {
                "to": [{"email": email}],
                "subject": "Verify your email address",
            }
        ],
        "from": {"email": sender},
        "content": [
            {
                "type": "text/plain",
                "value": (
                    f"Hello {full_name},\n\n"
                    "Thank you for registering! "
                    "Please verify your email by clicking the link below:\n\n"
                    f"{verification_link}\n\n"
                    "If you didn't register, please ignore this email.\n"
                ),
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {sg_api_key}",
        "Content-Type": "application/json",
    }

    sendgrid_url = "https://api.sendgrid.com/v3/mail/send"

    try:
        # Use a short timeout and do not stream large responses
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(sendgrid_url, headers=headers, json=payload)

        if resp.status_code in (200, 202):
            logger.info("Verification email queued/sent for %s", email)
            return True

        # Log non-sensitive parts of the error
        logger.warning(
            "Failed to send verification email to %s. status=%s response=%s",
            email,
            resp.status_code,
            resp.text[:1000],
        )
        return False

    except httpx.RequestError as exc:
        logger.error(
            "Error sending verification email to %s: %s",
            email,
            str(exc),
            exc_info=True
        )
        return False

"""
Email service for sending verification and notification emails.
"""
import logging
from typing import Optional
import logging
import json
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
        logger.warning("SendGrid not configured (missing SENDGRID_API_KEY or EMAILS_FROM). Email not sent.")
        return False

    if base_url is None:
        base_url = settings.EMAIL_VERIFICATION_BASE_URL or "http://localhost:5173"

    verification_link = f"{base_url.rstrip('/')}/verify-email?token={token}"

    # Plain text content
    plain_text = (
        f"Hello {full_name},\n\n"
        "Thank you for registering! Please verify your email by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        "This link will expire in 24 hours.\n\n"
        "If you didn't register, please ignore this email.\n"
    )

    # HTML content with styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h1 style="color: #2c3e50; margin-bottom: 20px;">Welcome to {settings.PROJECT_NAME}!</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">Hello {full_name},</p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                Thank you for registering! To complete your registration and activate your account, 
                please verify your email address by clicking the button below:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" 
                   style="background-color: #3498db; color: white; padding: 14px 28px; text-decoration: none; 
                          border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 20px;">
                Or copy and paste this link into your browser:
            </p>
            <p style="font-size: 14px; color: #3498db; word-break: break-all; background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                {verification_link}
            </p>
            <p style="font-size: 14px; color: #e74c3c; margin-top: 20px;">
                ⚠️ This link will expire in 24 hours.
            </p>
            <p style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                If you didn't create an account, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

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
                "value": plain_text,
            },
            {
                "type": "text/html",
                "value": html_content,
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
        logger.error("Error sending verification email to %s: %s", email, str(exc), exc_info=True)
        return False

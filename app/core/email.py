"""
Email service for sending verification and notification emails.
"""
import logging
import base64
import html
import re
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def sanitize_for_email(text: str) -> str:
    """
    Sanitize text for use in email content and headers.
    Removes control characters and normalizes whitespace.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for email
    """
    if not text:
        return ""
    # Remove control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Replace newlines with spaces (for headers and single-line content)
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and special characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename with only alphanumeric, hyphens, underscores, and dots
    """
    if not filename:
        return "invoice.pdf"
    # Remove path separators and potentially dangerous characters
    filename = re.sub(r'[/\\:*?"<>|]', '', filename)
    # Allow only alphanumeric, hyphens, underscores, and dots
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Ensure it doesn't start with a dot (hidden file)
    filename = filename.lstrip('.')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename if filename else "invoice.pdf"


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
            "SendGrid not configured (missing SENDGRID_KEY or EMAILS_FROM).\
                Email not sent."
        )
        return False

    if base_url is None:
        base_url = settings.EMAIL_VERIFICATION_BASE_URL or \
            "http://localhost:5173"

    verification_link = f"{base_url.rstrip('/')}/verify-email?token={token}"

    # Plain text content
    plain_text = (
        f"Hello {full_name},\n\n"
        "Thank you for registering!\
            Please verify your email by clicking the link below:\n\n"
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
    <body style="font-family: Arial, sans-serif; line-height: 1.6;
    color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px;
        border-radius: 10px;">
            <h1 style="color: #2c3e50; margin-bottom: 20px;">
            Welcome to {settings.PROJECT_NAME}!</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">
            Hello {full_name},</p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                Thank you for registering!
                To complete your registration and activate your account,
                please verify your email address by clicking the button below:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}"
                   style="background-color: #3498db; color: white;
                   padding: 14px 28px;
                   text-decoration: none; border-radius: 5px; font-size: 16px;
                   font-weight: bold; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 20px;">
                Or copy and paste this link into your browser:
            </p>
            <p style="font-size: 14px; color: #3498db; word-break: break-all;
            background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                {verification_link}
            </p>
            <p style="font-size: 14px; color: #e74c3c; margin-top: 20px;">
                ⚠️ This link will expire in 24 hours.
            </p>
            <p style="font-size: 14px; color: #666; margin-top: 30px;
            padding-top: 20px; border-top: 1px solid #ddd;">
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
        logger.error(
            "Error sending verification email to %s: %s", email,
            str(exc), exc_info=True
        )
        return False


def send_invoice_email(
    email: str,
    customer_name: str,
    invoice_number: str,
    pdf_bytes: bytes,
    total_amount: str,
) -> bool:
    """
    Send an invoice PDF via email using SendGrid's Web API v3.

    This function sends an invoice PDF as an email attachment to the customer.
    It reads the SendGrid API key and sender address from settings.

    Args:
        email: Customer email address
        customer_name: Customer full name
        invoice_number: Invoice number for reference
        pdf_bytes: PDF file content as bytes
        total_amount: Formatted total amount (e.g., "$250.00")

    Returns:
        True if send request was accepted by SendGrid, False otherwise.
    """
    sg_api_key = settings.SENDGRID_API_KEY
    sender = settings.EMAILS_FROM

    if not sg_api_key or not sender:
        logger.warning(
            "SendGrid not configured (missing SENDGRID_API_KEY or "
            "EMAILS_FROM). Email not sent."
        )
        return False

    # Sanitize user-provided data
    safe_customer_name = sanitize_for_email(customer_name)
    safe_invoice_number = sanitize_for_email(invoice_number)
    safe_total_amount = sanitize_for_email(total_amount)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    # Plain text content
    plain_text = (
        f"Dear {safe_customer_name},\n\n"
        f"Thank you for your business!\n\n"
        f"Please find attached your invoice {safe_invoice_number} "
        f"for the amount of {safe_total_amount}.\n\n"
        "If you have any questions, please don't hesitate to contact us.\n\n"
        "Best regards,\n"
        f"{safe_project_name}"
    )

    # HTML content with styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;
    color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px;
        border-radius: 10px;">
            <h1 style="color: #2c3e50; margin-bottom: 20px;">
            Invoice from {html.escape(safe_project_name)}</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">
            Dear {html.escape(safe_customer_name)},</p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                Thank you for your business! Please find attached your invoice
                <strong>{
                    html.escape(safe_invoice_number)
                    }</strong> for the amount
                of <strong>{html.escape(safe_total_amount)}</strong>.
            </p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                If you have any questions about this invoice, please don't
                hesitate to contact us.
            </p>
            <p style="font-size: 14px; color: #666; margin-top: 30px;
            padding-top: 20px; border-top: 1px solid #ddd;">
                Best regards,<br>
                {html.escape(safe_project_name)}
            </p>
        </div>
    </body>
    </html>
    """

    # Encode PDF as base64 for SendGrid attachment
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    payload = {
        "personalizations": [
            {
                "to": [{"email": email}],
                "subject": (
                    f"Invoice {safe_invoice_number} from {safe_project_name}"
                ),
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
        "attachments": [
            {
                "content": pdf_base64,
                "type": "application/pdf",
                "filename": sanitize_filename(f"invoice_{invoice_number}.pdf"),
                "disposition": "attachment"
            }
        ]
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
            logger.info(
                "Invoice email queued/sent for %s (invoice: %s)",
                email, invoice_number
            )
            return True

        # Log non-sensitive parts of the error
        logger.warning(
            "Failed to send invoice email to %s. status=%s response=%s",
            email,
            resp.status_code,
            resp.text[:1000],
        )
        return False

    except httpx.RequestError as exc:
        logger.error(
            "Error sending invoice email to %s: %s", email,
            str(exc), exc_info=True
        )
        return False


def send_password_reset_email(
    email: str,
    token: str,
    full_name: str,
    base_url: Optional[str] = None,
) -> bool:
    """
    Send a password reset email using SendGrid's Web API v3.

    Args:
        email: Recipient email address
        token: Password reset token
        full_name: Recipient full name
        base_url: Optional base URL to build reset link; falls back to
            settings.EMAIL_VERIFICATION_BASE_URL

    Returns:
        True if send request was accepted by SendGrid, False otherwise.
    """
    sg_api_key = settings.SENDGRID_API_KEY
    sender = settings.EMAILS_FROM

    if not sg_api_key or not sender:
        logger.warning(
            "SendGrid not configured (missing SENDGRID_API_KEY or EMAILS_FROM).\
                Email not sent."
        )
        return False

    if base_url is None:
        base_url = settings.EMAIL_VERIFICATION_BASE_URL or \
            "http://localhost:5173"

    reset_link = f"{base_url.rstrip('/')}/reset-password?token={token}"

    # Sanitize user-provided data
    safe_full_name = sanitize_for_email(full_name)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    # Plain text content
    plain_text = (
        f"Hello {safe_full_name},\n\n"
        "We received a request to reset your password. "
        "If you made this request, click the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        "This link will expire in 30 minutes.\n\n"
        "If you didn't request a password reset, please ignore this email "
        "and your password will remain unchanged.\n\n"
        "For security reasons, we recommend that you:\n"
        "- Never share your password with anyone\n"
        "- Use a strong, unique password\n"
        "- Change your password regularly\n\n"
        f"Best regards,\n{safe_project_name}"
    )

    # HTML content with styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;
    color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px;
        border-radius: 10px;">
            <h1 style="color: #2c3e50; margin-bottom: 20px;">
            Password Reset Request</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">
            Hello {html.escape(safe_full_name)},</p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                We received a request to reset your password for your
                {html.escape(safe_project_name)} account.
                If you made this request, click the button below to reset your password:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}"
                   style="background-color: #e74c3c; color: white;
                   padding: 14px 28px;
                   text-decoration: none; border-radius: 5px; font-size: 16px;
                   font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 20px;">
                Or copy and paste this link into your browser:
            </p>
            <p style="font-size: 14px; color: #3498db; word-break: break-all;
            background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
                {reset_link}
            </p>
            <p style="font-size: 14px; color: #e74c3c; margin-top: 20px;">
                ⚠️ This link will expire in 30 minutes.
            </p>
            <p style="font-size: 14px; color: #666; margin-top: 30px;">
                If you didn't request a password reset, please ignore this email.
                Your password will remain unchanged.
            </p>
            <div style="margin-top: 30px; padding-top: 20px;
            border-top: 1px solid #ddd;">
                <p style="font-size: 14px; color: #666; font-weight: bold;">
                    Security Tips:
                </p>
                <ul style="font-size: 14px; color: #666;">
                    <li>Never share your password with anyone</li>
                    <li>Use a strong, unique password</li>
                    <li>Change your password regularly</li>
                </ul>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 30px;
            padding-top: 20px; border-top: 1px solid #ddd;">
                Best regards,<br>
                {html.escape(safe_project_name)}
            </p>
        </div>
    </body>
    </html>
    """

    payload = {
        "personalizations": [
            {
                "to": [{"email": email}],
                "subject": "Password Reset Request",
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
            logger.info("Password reset email queued/sent for %s", email)
            return True

        # Log non-sensitive parts of the error
        logger.warning(
            "Failed to send password reset email to %s. status=%s response=%s",
            email,
            resp.status_code,
            resp.text[:1000],
        )
        return False

    except httpx.RequestError as exc:
        logger.error(
            "Error sending password reset email to %s: %s", email,
            str(exc), exc_info=True
        )
        return False

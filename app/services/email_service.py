"""
Email service for composing and sending emails through providers.

This module provides high-level email composition functions that use
the modular email provider system. It separates email content generation
from the actual sending mechanism.
"""
from typing import Optional, Tuple
import logging
import html
import re

from app.core.config import settings
from app.services.email_provider import get_email_provider, EmailProvider

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


def get_configured_email_provider() -> Optional[EmailProvider]:
    """
    Get the configured email provider based on settings.

    Returns:
        EmailProvider instance or None if not configured
    """
    # Determine provider type from environment
    provider_type = getattr(
        settings, 'EMAIL_PROVIDER', 'sendgrid'
    ).lower()

    # For testing environment, use mock provider
    if settings.ENVIRONMENT == "testing":
        provider_type = "mock"

    try:
        if provider_type == "sendgrid":
            config = {
                "api_key": settings.SENDGRID_API_KEY,
                "from_email": settings.EMAILS_FROM,
            }
            provider = get_email_provider("sendgrid", config)

            # Validate configuration
            if not provider.validate_configuration():
                logger.warning(
                    "SendGrid provider not properly configured"
                )
                return None

            return provider

        elif provider_type == "mock":
            return get_email_provider("mock")

        else:
            logger.warning(
                "Unknown email provider type: %s", provider_type
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to initialize email provider: %s", str(e),
            exc_info=True
        )
        return None


def compose_verification_email(
    full_name: str,
    verification_link: str,
) -> Tuple[str, str]:
    """
    Compose verification email content.

    Args:
        full_name: Recipient's full name
        verification_link: Verification URL

    Returns:
        Tuple of (plain_text, html_content)
    """
    # Sanitize inputs
    safe_full_name = sanitize_for_email(full_name)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    # Plain text content
    plain_text = (
        f"Hello {safe_full_name},\n\n"
        "Thank you for registering! "
        "Please verify your email by clicking the link below:\n\n"
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
            Welcome to {html.escape(safe_project_name)}!</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">
            Hello {html.escape(safe_full_name)},</p>
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

    return plain_text, html_content


def compose_password_reset_email(
    full_name: str,
    reset_link: str,
) -> Tuple[str, str]:
    """
    Compose password reset email content.

    Args:
        full_name: Recipient's full name
        reset_link: Password reset URL

    Returns:
        Tuple of (plain_text, html_content)
    """
    safe_full_name = sanitize_for_email(full_name)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    plain_text = (
        f"Hello {safe_full_name},\n\n"
        "We received a request to reset your password. "
        "If you made this request, click the link below to reset your "
        "password:\n\n"
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
                If you made this request, click the button below to reset
                your password:
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
                If you didn't request a password reset, please ignore this.
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

    return plain_text, html_content


def compose_verification_reminder_email(
    full_name: str,
    verification_link: str,
) -> Tuple[str, str]:
    """
    Compose verification reminder email content.

    Args:
        full_name: Recipient's full name
        verification_link: Verification URL

    Returns:
        Tuple of (plain_text, html_content)
    """
    safe_full_name = sanitize_for_email(full_name)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    plain_text = (
        f"Hello {safe_full_name},\n\n"
        "We noticed that you haven't verified your email address yet.\n\n"
        "Verifying your email is important to ensure you can:\n"
        "- Create and send invoices\n"
        "- Access all features of your account\n"
        "- Receive important notifications\n\n"
        "Please verify your email by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        "This link will expire in 24 hours.\n\n"
        "If you didn't register, please ignore this email.\n\n"
        f"Best regards,\n{safe_project_name}"
    )

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
            Verify Your Email Address</h1>
            <p style="font-size: 16px; margin-bottom: 20px;">
            Hello {html.escape(safe_full_name)},</p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                We noticed that you haven't verified your email address yet.
            </p>
            <p style="font-size: 16px; margin-bottom: 20px;">
                Verifying your email is important to ensure you can:
            </p>
            <ul style="font-size: 16px; margin-bottom: 20px;">
                <li>Create and send invoices</li>
                <li>Access all features of your account</li>
                <li>Receive important notifications</li>
            </ul>
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
            <p style="font-size: 14px; color: #666; margin-top: 20px;">
                Best regards,<br>
                {html.escape(safe_project_name)}
            </p>
        </div>
    </body>
    </html>
    """

    return plain_text, html_content


def compose_invoice_email(
    customer_name: str,
    invoice_number: str,
    total_amount: str,
) -> Tuple[str, str]:
    """
    Compose invoice email content.

    Args:
        customer_name: Customer's name
        invoice_number: Invoice number
        total_amount: Formatted total amount

    Returns:
        Tuple of (plain_text, html_content)
    """
    safe_customer_name = sanitize_for_email(customer_name)
    safe_invoice_number = sanitize_for_email(invoice_number)
    safe_total_amount = sanitize_for_email(total_amount)
    safe_project_name = sanitize_for_email(settings.PROJECT_NAME)

    plain_text = (
        f"Dear {safe_customer_name},\n\n"
        f"Thank you for your business!\n\n"
        f"Please find attached your invoice {safe_invoice_number} "
        f"for the amount of {safe_total_amount}.\n\n"
        "If you have any questions, please don't hesitate to contact us.\n\n"
        "Best regards,\n"
        f"{safe_project_name}"
    )

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
                <strong>{html.escape(safe_invoice_number)}</strong> for
                    the amount
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

    return plain_text, html_content

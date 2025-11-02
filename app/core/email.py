"""
Email service for sending verification and notification emails.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_verification_email(
    email: str,
    token: str,
    full_name: str,
    base_url: Optional[str] = None
) -> bool:
    """
    Send a verification email to a new user.
    
    Args:
        email: Recipient email address
        token: Verification token
        full_name: User's full name
        base_url: Base URL for the verification link (optional)
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Default base URL if not provided
    if base_url is None:
        base_url = "https://yourapp.com"
    
    verification_link = f"{base_url}/verify-email?token={token}"
    
    # For now, log the email (placeholder for actual email sending)
    # In a production environment, this would integrate with an email service
    # like SendGrid, AWS SES, or similar
    logger.info(
        f"[EMAIL] Verification email for {email}\n"
        f"To: {email}\n"
        f"Subject: Verify your email address\n"
        f"Body:\n"
        f"Hello {full_name},\n\n"
        f"Thank you for registering! Please verify your email by clicking:\n"
        f"{verification_link}\n\n"
        f"If you didn't register, please ignore this email.\n"
    )
    
    # Return True to indicate the email would be sent in production
    # In a real implementation, this would return the result of the actual email send
    return True

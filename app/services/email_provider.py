"""
Email provider interface and implementations for modular email sending.

This module provides a plug-and-play email system that allows easy switching
between different email providers (SendGrid, AWS SES, SMTP, etc.) without
impacting the rest of the application logic.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging
import base64

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """
    Abstract base class for email providers.

    All email providers must implement this interface to ensure
    modularity and easy swapping of email backends.
    """

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: Optional[str] = None,
        attachments: Optional[list] = None,
        **kwargs
    ) -> bool:
        """
        Send an email using the provider's API.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            plain_text: Plain text email body
            html_content: Optional HTML email body
            attachments: Optional list of attachments (dicts with content,
                        type, filename)
            **kwargs: Additional provider-specific parameters

        Returns:
            True if email was successfully queued/sent, False otherwise
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the provider is properly configured.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass


class SendGridEmailProvider(EmailProvider):
    """SendGrid email provider implementation."""

    def __init__(self, api_key: str, from_email: str):
        """
        Initialize SendGrid provider.

        Args:
            api_key: SendGrid API key
            from_email: Sender email address
        """
        self.api_key = api_key
        self.from_email = from_email

    def validate_configuration(self) -> bool:
        """Validate SendGrid configuration."""
        if not self.api_key or not self.from_email:
            logger.warning(
                "SendGrid not configured (missing API key or from_email)"
            )
            return False
        return True

    def send_email(
        self,
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: Optional[str] = None,
        attachments: Optional[list] = None,
        **kwargs
    ) -> bool:
        """
        Send email using SendGrid API v3.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            plain_text: Plain text email body
            html_content: Optional HTML email body
            attachments: Optional list of dicts with keys:
                        - content: base64 encoded content or bytes
                        - type: MIME type
                        - filename: attachment filename
            **kwargs: Additional SendGrid parameters

        Returns:
            True if send request was accepted, False otherwise
        """
        import httpx

        if not self.validate_configuration():
            return False

        # Build email payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject,
                }
            ],
            "from": {"email": self.from_email},
            "content": [
                {
                    "type": "text/plain",
                    "value": plain_text,
                }
            ],
        }

        # Add HTML content if provided
        if html_content:
            payload["content"].append({
                "type": "text/html",
                "value": html_content,
            })

        # Add attachments if provided
        if attachments:
            payload["attachments"] = []
            for attachment in attachments:
                content = attachment.get("content", b"")
                # Convert bytes to base64 if needed
                if isinstance(content, bytes):
                    content = base64.b64encode(content).decode('utf-8')

                payload["attachments"].append({
                    "content": content,
                    "type": attachment.get("type", "application/octet-stream"),
                    "filename": attachment.get("filename", "attachment"),
                    "disposition": attachment.get("disposition", "attachment")
                })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        sendgrid_url = "https://api.sendgrid.com/v3/mail/send"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(sendgrid_url, headers=headers, json=payload)

            if resp.status_code in (200, 202):
                logger.info("Email queued/sent to %s via SendGrid", to_email)
                return True

            logger.warning(
                "Failed to send email to %s. status=%s response=%s",
                to_email,
                resp.status_code,
                resp.text[:1000],
            )
            return False

        except Exception as exc:
            logger.error(
                "Error sending email to %s: %s", to_email,
                str(exc), exc_info=True
            )
            return False


class MockEmailProvider(EmailProvider):
    """
    Mock email provider for testing and development.

    This provider logs emails instead of sending them, useful for
    development and testing environments.
    """

    def __init__(self):
        """Initialize mock provider."""
        self.sent_emails = []

    def validate_configuration(self) -> bool:
        """Mock provider is always valid."""
        return True

    def send_email(
        self,
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: Optional[str] = None,
        attachments: Optional[list] = None,
        **kwargs
    ) -> bool:
        """
        Mock send email - logs instead of sending.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            plain_text: Plain text email body
            html_content: Optional HTML email body
            attachments: Optional list of attachments
            **kwargs: Additional parameters (ignored)

        Returns:
            Always returns True
        """
        email_data = {
            "to": to_email,
            "subject": subject,
            "plain_text": plain_text,
            "html_content": html_content,
            "attachments": attachments,
        }
        self.sent_emails.append(email_data)

        logger.info(
            "MOCK EMAIL - To: %s, Subject: %s",
            to_email, subject
        )
        logger.debug("MOCK EMAIL content: %s", plain_text[:200])

        return True

    def get_sent_emails(self) -> list:
        """Get list of sent emails (for testing)."""
        return self.sent_emails

    def clear_sent_emails(self):
        """Clear sent emails history (for testing)."""
        self.sent_emails = []


def get_email_provider(
    provider_type: str = "sendgrid",
    config: Optional[Dict[str, Any]] = None
) -> EmailProvider:
    """
    Factory function to get email provider instance.

    Args:
        provider_type: Type of provider ("sendgrid", "mock", etc.)
        config: Provider configuration dictionary

    Returns:
        EmailProvider instance

    Raises:
        ValueError: If provider_type is not supported
    """
    config = config or {}

    if provider_type == "sendgrid":
        api_key = config.get("api_key", "")
        from_email = config.get("from_email", "")
        return SendGridEmailProvider(api_key, from_email)

    elif provider_type == "mock":
        return MockEmailProvider()

    else:
        raise ValueError(
            f"Unsupported email provider: {provider_type}. "
            f"Supported providers: sendgrid, mock"
        )

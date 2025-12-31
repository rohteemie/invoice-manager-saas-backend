"""
Progressive login delay/throttling service.

Implements per-account throttling to prevent credential stuffing and
brute-force attacks while maintaining constant-time responses.
Complies with OWASP ASVS V2.1.7, V2.2.2, V2.2.5 and NIST SP 800-63B.
"""
import asyncio
import logging
import time
from typing import Optional, Tuple
from app.core.cache import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class LoginThrottle:
    """
    Per-account login throttling with progressive delays.

    Uses Redis for distributed state management.
    Falls back gracefully if Redis is unavailable.
    """

    def __init__(self):
        """Initialize the login throttle service."""
        self.redis_client = get_redis_client()

    def _get_failure_key(self, email: str) -> str:
        """Generate Redis key for failed login counter."""
        return f"login:failures:{email.lower()}"

    def _get_cooldown_key(self, email: str) -> str:
        """Generate Redis key for cooldown expiry timestamp."""
        return f"login:cooldown:{email.lower()}"

    def get_failed_attempts(self, email: str) -> int:
        """
        Get number of failed login attempts for an account.

        Args:
            email: User email address

        Returns:
            Number of failed attempts (0 if Redis unavailable)
        """
        if not self.redis_client:
            return 0

        try:
            key = self._get_failure_key(email)
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.warning(f"Failed to get login attempts: {e}")
            return 0

    def record_failed_attempt(self, email: str) -> int:
        """
        Record a failed login attempt and return current count.

        Args:
            email: User email address

        Returns:
            Total number of failed attempts after this one
        """
        if not self.redis_client:
            return 0

        try:
            key = self._get_failure_key(email)
            # Increment counter and set expiry
            count = self.redis_client.incr(key)
            # Set TTL if this is the first failure
            if count == 1:
                self.redis_client.expire(
                    key, settings.LOGIN_FAILURE_WINDOW
                )
            return count
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            return 0

    def clear_failed_attempts(self, email: str) -> bool:
        """
        Clear failed login attempts counter (called on successful login).

        Args:
            email: User email address

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            failure_key = self._get_failure_key(email)
            cooldown_key = self._get_cooldown_key(email)
            self.redis_client.delete(failure_key)
            self.redis_client.delete(cooldown_key)
            return True
        except Exception as e:
            logger.error(f"Failed to clear login attempts: {e}")
            return False

    def get_delay_seconds(self, failed_attempts: int) -> int:
        """
        Calculate delay in seconds based on failed attempts.

        Progressive delay policy:
        - 1-3 attempts: No delay
        - 4-5 attempts: Short delay (default 2s)
        - 6-8 attempts: Medium delay (default 30s)
        - 9+ attempts: Long delay (default 15min)

        Args:
            failed_attempts: Number of failed login attempts

        Returns:
            Delay in seconds to apply
        """
        if failed_attempts < settings.LOGIN_DELAY_THRESHOLD_SHORT:
            return 0
        elif failed_attempts < settings.LOGIN_DELAY_THRESHOLD_MEDIUM:
            return settings.LOGIN_DELAY_SHORT
        elif failed_attempts < settings.LOGIN_DELAY_THRESHOLD_LONG:
            return settings.LOGIN_DELAY_MEDIUM
        else:
            return settings.LOGIN_DELAY_LONG

    def is_in_cooldown(self, email: str) -> Tuple[bool, int]:
        """
        Check if account is in cooldown period.

        Args:
            email: User email address

        Returns:
            Tuple of (is_in_cooldown, remaining_seconds)
        """
        if not self.redis_client:
            return False, 0

        try:
            key = self._get_cooldown_key(email)
            cooldown_until = self.redis_client.get(key)
            if not cooldown_until:
                return False, 0

            remaining = int(float(cooldown_until)) - int(time.time())
            if remaining > 0:
                return True, remaining
            else:
                # Cooldown expired, clean up
                self.redis_client.delete(key)
                return False, 0
        except Exception as e:
            logger.error(f"Failed to check cooldown: {e}")
            return False, 0

    def set_cooldown(self, email: str, delay_seconds: int) -> bool:
        """
        Set a cooldown period for an account.

        Args:
            email: User email address
            delay_seconds: Duration of cooldown in seconds

        Returns:
            True if set successfully, False otherwise
        """
        if not self.redis_client or delay_seconds <= 0:
            return False

        try:
            key = self._get_cooldown_key(email)
            cooldown_until = time.time() + delay_seconds
            self.redis_client.setex(
                key, delay_seconds, str(cooldown_until)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set cooldown: {e}")
            return False

    async def apply_delay(
        self, email: str, failed_attempts: int
    ) -> Tuple[int, int]:
        """
        Apply progressive delay based on failed attempts.

        This enforces server-side delay to slow down attackers.
        Always returns the same delay for a given attempt count
        to avoid timing leaks.

        Args:
            email: User email address
            failed_attempts: Number of failed login attempts

        Returns:
            Tuple of (delay_applied_seconds, remaining_cooldown_seconds)
        """
        # Check if already in cooldown
        in_cooldown, remaining = self.is_in_cooldown(email)
        if in_cooldown:
            # Already in cooldown, don't apply additional delay
            return 0, remaining

        # Calculate delay for this attempt count
        delay = self.get_delay_seconds(failed_attempts)

        if delay > 0:
            # Set cooldown for future attempts
            self.set_cooldown(email, delay)

            # Apply immediate delay
            await asyncio.sleep(delay)

        return delay, delay if delay > 0 else 0

    def get_throttle_status(self, email: str) -> dict:
        """
        Get current throttle status for an account.

        Useful for monitoring and alerting.

        Args:
            email: User email address

        Returns:
            Dictionary with throttle status information
        """
        failed_attempts = self.get_failed_attempts(email)
        in_cooldown, remaining = self.is_in_cooldown(email)
        delay = self.get_delay_seconds(failed_attempts)

        return {
            "email": email,
            "failed_attempts": failed_attempts,
            "in_cooldown": in_cooldown,
            "cooldown_remaining_seconds": remaining,
            "next_delay_seconds": delay,
            "is_locked": failed_attempts >= settings.LOGIN_DELAY_THRESHOLD_LONG
        }


# Singleton instance
_throttle_instance: Optional[LoginThrottle] = None


def get_login_throttle() -> LoginThrottle:
    """Get or create the login throttle singleton instance."""
    global _throttle_instance
    if _throttle_instance is None:
        _throttle_instance = LoginThrottle()
    return _throttle_instance

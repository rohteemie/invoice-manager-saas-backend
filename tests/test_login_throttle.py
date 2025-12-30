"""
Test suite for progressive login delay/throttling.
Tests per-account throttling, progressive delays, and OWASP ASVS compliance.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
from app.core.login_throttle import LoginThrottle, get_login_throttle
from app.core.config import settings


@pytest.fixture
def throttle():
    """Create a login throttle instance for testing."""
    return LoginThrottle()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.incr.return_value = 1
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.expire.return_value = True
    return mock


def test_get_login_throttle_singleton():
    """Test that get_login_throttle returns singleton instance."""
    throttle1 = get_login_throttle()
    throttle2 = get_login_throttle()
    assert throttle1 is throttle2


def test_get_failed_attempts_no_redis(throttle):
    """Test getting failed attempts when Redis is unavailable."""
    throttle.redis_client = None
    assert throttle.get_failed_attempts("test@example.com") == 0


def test_get_failed_attempts_with_redis(throttle, mock_redis):
    """Test getting failed attempts with Redis."""
    throttle.redis_client = mock_redis
    mock_redis.get.return_value = "5"

    attempts = throttle.get_failed_attempts("test@example.com")
    assert attempts == 5
    mock_redis.get.assert_called_once()


def test_record_failed_attempt_no_redis(throttle):
    """Test recording failed attempt when Redis is unavailable."""
    throttle.redis_client = None
    assert throttle.record_failed_attempt("test@example.com") == 0


def test_record_failed_attempt_first_failure(throttle, mock_redis):
    """Test recording first failed attempt sets TTL."""
    throttle.redis_client = mock_redis
    mock_redis.incr.return_value = 1

    count = throttle.record_failed_attempt("test@example.com")
    assert count == 1
    mock_redis.expire.assert_called_once()


def test_record_failed_attempt_subsequent_failures(throttle, mock_redis):
    """Test recording subsequent failed attempts."""
    throttle.redis_client = mock_redis
    mock_redis.incr.return_value = 3

    count = throttle.record_failed_attempt("test@example.com")
    assert count == 3


def test_clear_failed_attempts_no_redis(throttle):
    """Test clearing attempts when Redis is unavailable."""
    throttle.redis_client = None
    assert throttle.clear_failed_attempts("test@example.com") is False


def test_clear_failed_attempts_with_redis(throttle, mock_redis):
    """Test clearing failed attempts with Redis."""
    throttle.redis_client = mock_redis

    result = throttle.clear_failed_attempts("test@example.com")
    assert result is True
    assert mock_redis.delete.call_count == 2  # failure and cooldown keys


def test_get_delay_seconds_no_delay():
    """Test delay calculation for 1-3 attempts (no delay)."""
    throttle = LoginThrottle()
    assert throttle.get_delay_seconds(1) == 0
    assert throttle.get_delay_seconds(3) == 0


def test_get_delay_seconds_short_delay():
    """Test delay calculation for 4-5 attempts (short delay)."""
    throttle = LoginThrottle()
    delay = throttle.get_delay_seconds(4)
    assert delay == settings.LOGIN_DELAY_SHORT
    assert throttle.get_delay_seconds(5) == settings.LOGIN_DELAY_SHORT


def test_get_delay_seconds_medium_delay():
    """Test delay calculation for 6-8 attempts (medium delay)."""
    throttle = LoginThrottle()
    delay = throttle.get_delay_seconds(6)
    assert delay == settings.LOGIN_DELAY_MEDIUM
    assert throttle.get_delay_seconds(8) == settings.LOGIN_DELAY_MEDIUM


def test_get_delay_seconds_long_delay():
    """Test delay calculation for 9+ attempts (long delay)."""
    throttle = LoginThrottle()
    delay = throttle.get_delay_seconds(9)
    assert delay == settings.LOGIN_DELAY_LONG
    assert throttle.get_delay_seconds(15) == settings.LOGIN_DELAY_LONG


def test_is_in_cooldown_no_redis(throttle):
    """Test cooldown check when Redis is unavailable."""
    throttle.redis_client = None
    in_cooldown, remaining = throttle.is_in_cooldown("test@example.com")
    assert in_cooldown is False
    assert remaining == 0


def test_is_in_cooldown_not_set(throttle, mock_redis):
    """Test cooldown check when no cooldown is set."""
    throttle.redis_client = mock_redis
    mock_redis.get.return_value = None

    in_cooldown, remaining = throttle.is_in_cooldown("test@example.com")
    assert in_cooldown is False
    assert remaining == 0


def test_is_in_cooldown_active(throttle, mock_redis):
    """Test cooldown check when cooldown is active."""
    throttle.redis_client = mock_redis
    future_time = str(time.time() + 60)
    mock_redis.get.return_value = future_time

    in_cooldown, remaining = throttle.is_in_cooldown("test@example.com")
    assert in_cooldown is True
    assert remaining > 0
    assert remaining <= 60


def test_is_in_cooldown_expired(throttle, mock_redis):
    """Test cooldown check when cooldown has expired."""
    throttle.redis_client = mock_redis
    past_time = str(time.time() - 10)
    mock_redis.get.return_value = past_time

    in_cooldown, remaining = throttle.is_in_cooldown("test@example.com")
    assert in_cooldown is False
    assert remaining == 0
    mock_redis.delete.assert_called_once()


def test_set_cooldown_no_redis(throttle):
    """Test setting cooldown when Redis is unavailable."""
    throttle.redis_client = None
    assert throttle.set_cooldown("test@example.com", 60) is False


def test_set_cooldown_with_redis(throttle, mock_redis):
    """Test setting cooldown with Redis."""
    throttle.redis_client = mock_redis

    result = throttle.set_cooldown("test@example.com", 60)
    assert result is True
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_apply_delay_no_delay(throttle, mock_redis):
    """Test applying delay with no failed attempts."""
    throttle.redis_client = mock_redis
    mock_redis.get.return_value = None

    start_time = time.time()
    delay_applied, remaining = await throttle.apply_delay(
        "test@example.com", 2
    )
    elapsed = time.time() - start_time

    assert delay_applied == 0
    assert remaining == 0
    assert elapsed < 1  # Should be nearly instant


@pytest.mark.asyncio
async def test_apply_delay_already_in_cooldown(throttle, mock_redis):
    """Test applying delay when already in cooldown."""
    throttle.redis_client = mock_redis
    future_time = str(time.time() + 30)
    mock_redis.get.return_value = future_time

    start_time = time.time()
    delay_applied, remaining = await throttle.apply_delay(
        "test@example.com", 5
    )
    elapsed = time.time() - start_time

    assert delay_applied == 0
    assert remaining > 0
    assert elapsed < 1  # Should not add delay if already in cooldown


@pytest.mark.asyncio
async def test_apply_delay_short_delay(throttle, mock_redis):
    """Test applying short delay for 4-5 attempts."""
    throttle.redis_client = mock_redis
    # Not in cooldown
    mock_redis.get.return_value = None

    # Use very short delay for testing
    with patch.object(
        throttle, 'get_delay_seconds', return_value=0.1
    ):
        start_time = time.time()
        delay_applied, remaining = await throttle.apply_delay(
            "test@example.com", 4
        )
        elapsed = time.time() - start_time

        assert delay_applied == 0.1
        assert remaining == 0.1
        assert elapsed >= 0.1


def test_get_throttle_status(throttle, mock_redis):
    """Test getting throttle status for an account."""
    throttle.redis_client = mock_redis
    mock_redis.get.side_effect = [
        "5",  # failed attempts
        None  # not in cooldown
    ]

    status = throttle.get_throttle_status("test@example.com")

    assert status["email"] == "test@example.com"
    assert status["failed_attempts"] == 5
    assert status["in_cooldown"] is False
    assert status["cooldown_remaining_seconds"] == 0
    assert status["next_delay_seconds"] == settings.LOGIN_DELAY_SHORT
    assert status["is_locked"] is False


def test_get_throttle_status_locked(throttle, mock_redis):
    """Test throttle status when account is locked (9+ attempts)."""
    throttle.redis_client = mock_redis
    mock_redis.get.side_effect = [
        "10",  # failed attempts
        str(time.time() + 600)  # in cooldown
    ]

    status = throttle.get_throttle_status("test@example.com")

    assert status["failed_attempts"] == 10
    assert status["in_cooldown"] is True
    assert status["is_locked"] is True


def test_email_normalization(throttle, mock_redis):
    """Test that email addresses are normalized to lowercase."""
    throttle.redis_client = mock_redis
    mock_redis.incr.return_value = 1

    # Record with mixed case
    throttle.record_failed_attempt("Test@Example.COM")

    # Verify key uses lowercase
    expected_key = "login:failures:test@example.com"
    mock_redis.incr.assert_called_with(expected_key)


def test_failure_keys_isolated(throttle):
    """Test that different emails have isolated failure counters."""
    key1 = throttle._get_failure_key("user1@example.com")
    key2 = throttle._get_failure_key("user2@example.com")
    assert key1 != key2
    assert "user1@example.com" in key1
    assert "user2@example.com" in key2


def test_cooldown_keys_isolated(throttle):
    """Test that different emails have isolated cooldown keys."""
    key1 = throttle._get_cooldown_key("user1@example.com")
    key2 = throttle._get_cooldown_key("user2@example.com")
    assert key1 != key2
    assert "user1@example.com" in key1
    assert "user2@example.com" in key2

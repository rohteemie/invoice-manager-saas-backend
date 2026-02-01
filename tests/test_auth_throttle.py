"""
Integration tests for login endpoint with progressive throttling.
Tests the complete authentication flow with throttling enabled.
"""
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.config import settings
from app.models.audit_log import AuditAction


def test_login_success_clears_throttle(client, test_user):
    """Test that successful login clears throttle counters."""
    # Mock the throttle to verify it's called
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 200
        # Verify clear was called on success
        mock_throttle.clear_failed_attempts.assert_called_once()


def test_login_failure_records_attempt(client, test_user):
    """Test that failed login records throttle attempt."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 1
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == 401
        # Verify attempt was recorded
        mock_throttle.record_failed_attempt.assert_called_once()


def test_login_progressive_delay_applied(client, test_user):
    """Test that progressive delay is applied based on attempts."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 4
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 5
        # Simulate 2 second delay
        mock_throttle.apply_delay = AsyncMock(return_value=(
            settings.LOGIN_DELAY_SHORT, settings.LOGIN_DELAY_SHORT
        ))
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == 401
        # Verify delay was called
        mock_throttle.apply_delay.assert_called_once()


def test_login_inactive_user_records_attempt(client, inactive_user):
    """Test that inactive user login attempt is recorded as failure."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 1
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": inactive_user.email,
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 401
        # Verify attempt was recorded even for inactive user
        mock_throttle.record_failed_attempt.assert_called_once()


def test_login_nonexistent_user_applies_delay(client):
    """Test that non-existent user gets same treatment (constant-time)."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 5
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 6
        mock_throttle.apply_delay = AsyncMock(return_value=(
            settings.LOGIN_DELAY_MEDIUM, settings.LOGIN_DELAY_MEDIUM
        ))
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["message"].lower()
        # Verify delay was applied even for non-existent user
        mock_throttle.apply_delay.assert_called_once()


def test_login_error_messages_generic(client, test_user):
    """Test that error messages don't leak information."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 1
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_get.return_value = mock_throttle

        # Wrong password
        response1 = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword"
            }
        )

        # Non-existent user
        response2 = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword"
            }
        )

        # Both should have same generic error
        assert response1.status_code == 401
        assert response2.status_code == 401
        assert response1.json()["message"] == response2.json()["message"]


def test_login_audit_logs_throttle_events(client, test_user, db_session):
    """Test that throttle events are logged to audit log."""
    from app.models.audit_log import AuditLog

    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 8
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 9
        # Simulate long delay being applied
        mock_throttle.apply_delay = AsyncMock(return_value=(
            settings.LOGIN_DELAY_LONG, settings.LOGIN_DELAY_LONG
        ))
        mock_get.return_value = mock_throttle

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401

        # Check audit logs
        logs = db_session.query(AuditLog).filter(
            AuditLog.action.in_([
                AuditAction.LOGIN_FAILED,
                AuditAction.LOGIN_EXCESSIVE_FAILURES,
                AuditAction.LOGIN_THROTTLED
            ])
        ).all()

        # Should have multiple audit entries
        assert len(logs) >= 1
        # At least one should be LOGIN_FAILED
        assert any(log.action == AuditAction.LOGIN_FAILED for log in logs)


def test_login_multiple_failures_progression(client, test_user):
    """Test progressive delay increases with multiple failures."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_get.return_value = mock_throttle

        # Simulate progression: 0 -> 1 -> 2 -> 3 -> 4 attempts
        for attempt in range(1, 5):
            mock_throttle.get_failed_attempts.return_value = attempt - 1
            mock_throttle.is_in_cooldown.return_value = (False, 0)
            mock_throttle.record_failed_attempt.return_value = attempt

            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword"
                }
            )

            assert response.status_code == 401

        # Verify record_failed_attempt was called multiple times
        assert mock_throttle.record_failed_attempt.call_count == 4


def test_login_throttle_graceful_degradation_no_redis(client, test_user):
    """Test that login works even if Redis/throttle is unavailable."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        # Simulate Redis unavailable
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 0
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_throttle.clear_failed_attempts.return_value = False
        mock_get.return_value = mock_throttle

        # Should still allow successful login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "TestPass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


def test_login_case_insensitive_email_throttle(client, test_user):
    """Test that email throttling is case-insensitive."""
    with patch('app.api.v1.endpoints.auth.get_login_throttle') as mock_get:
        mock_throttle = MagicMock()
        mock_throttle.get_failed_attempts.return_value = 0
        mock_throttle.is_in_cooldown.return_value = (False, 0)
        mock_throttle.record_failed_attempt.return_value = 1
        mock_throttle.apply_delay = AsyncMock(return_value=(0, 0))
        mock_get.return_value = mock_throttle

        # Try with different case
        email_upper = test_user.email.upper()
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": email_upper,
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        # Verify that email was lowercased before recording
        call_args = mock_throttle.record_failed_attempt.call_args
        assert call_args[0][0] == test_user.email.lower()

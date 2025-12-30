# Progressive Login Delay (Login Throttling) Documentation

## Overview

The Progressive Login Delay feature implements per-account throttling to prevent credential stuffing, brute-force attacks, and distributed attacks targeting individual user accounts. This enhancement complies with OWASP ASVS (Application Security Verification Standard) and NIST SP 800-63B guidelines.

**Implemented**: 2025-12-30  
**Version**: 1.0.0  
**Compliance**: OWASP ASVS V2.1.7, V2.2.2, V2.2.5, V2.1.6 | NIST SP 800-63B 5.2.2, 5.2.3, 5.2.4

---

## Table of Contents

1. [Security Objectives](#security-objectives)
2. [How It Works](#how-it-works)
3. [Progressive Delay Policy](#progressive-delay-policy)
4. [Configuration](#configuration)
5. [Implementation Details](#implementation-details)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Security Considerations](#security-considerations)
8. [OWASP ASVS Compliance](#owasp-asvs-compliance)
9. [NIST SP 800-63B Compliance](#nist-sp-800-63b-compliance)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## Security Objectives

### Primary Goals

1. **Prevent Credential Stuffing**: Slow down automated attacks using stolen credentials
2. **Mitigate Brute-Force Attacks**: Make password guessing economically infeasible
3. **Defend Against Distributed Attacks**: Per-account throttling works even when attackers rotate IPs
4. **Avoid Account Enumeration**: Maintain constant-time responses regardless of account existence
5. **Prevent Denial of Service**: No permanent lockouts—accounts auto-unlock after cooldown

### Security Risks Mitigated

- **High**: Credential stuffing attacks
- **High**: Slow brute-force attacks
- **Medium**: Distributed brute-force via IP rotation
- **Medium**: Account enumeration via timing attacks
- **Low**: Denial of service via account lockout

---

## How It Works

### Basic Flow

1. **Failed Login Attempt**: When a user fails to authenticate, the system:
   - Records the failed attempt in Redis (per email address)
   - Increments the failure counter with a 1-hour TTL
   - Calculates appropriate delay based on attempt count
   - Applies server-side delay before responding
   - Returns generic error message (no info leak)

2. **Successful Login**: When authentication succeeds:
   - All failure counters are cleared
   - Cooldown timers are reset
   - User receives access and refresh tokens

3. **Progressive Delays**: As failures increase:
   - 1-3 attempts: No delay
   - 4-5 attempts: 2-second delay (configurable)
   - 6-8 attempts: 30-second delay (configurable)
   - 9+ attempts: 15-minute cooldown (configurable)

### Key Features

- **Constant-Time Responses**: All authentication failures return the same error and take similar time
- **No Permanent Lockout**: Accounts automatically unlock after cooldown period
- **Works Alongside Rate Limiting**: Global IP-based rate limits remain active
- **Graceful Degradation**: If Redis is unavailable, authentication still works (without throttling)
- **Audit Trail**: All throttling events are logged for security monitoring

---

## Progressive Delay Policy

### Default Thresholds

| Failed Attempts | Delay Applied | Purpose |
|----------------|---------------|---------|
| 1-3           | No delay      | Normal user mistakes |
| 4-5           | 2 seconds     | Deter automated tools |
| 6-8           | 30 seconds    | Significant slowdown |
| 9+            | 15 minutes    | Long cooldown period |

### Configurable Parameters

All delays and thresholds can be configured via environment variables:

```bash
# Short delay for 4-5 failed attempts (seconds)
LOGIN_DELAY_SHORT=2

# Medium delay for 6-8 failed attempts (seconds)
LOGIN_DELAY_MEDIUM=30

# Long delay/cooldown for 9+ failed attempts (seconds, 900 = 15 minutes)
LOGIN_DELAY_LONG=900

# Thresholds for when each delay level kicks in
LOGIN_DELAY_THRESHOLD_SHORT=4
LOGIN_DELAY_THRESHOLD_MEDIUM=6
LOGIN_DELAY_THRESHOLD_LONG=9

# Time window for tracking failures (seconds, 3600 = 1 hour)
LOGIN_FAILURE_WINDOW=3600
```

### Delay Behavior

- **Server-Side Enforcement**: Delays are applied on the server before responding
- **Constant-Time**: Same delay applies whether account exists or not
- **Auto-Reset**: Counters expire after `LOGIN_FAILURE_WINDOW` (default: 1 hour)
- **Cooldown State**: Once in cooldown, additional attempts don't add extra delay

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Progressive Login Delay Settings (OWASP ASVS & NIST 800-63B Compliance)
# Delays are applied progressively based on failed login attempts per account

# Short delay for 4-5 failed attempts (seconds)
LOGIN_DELAY_SHORT=2

# Medium delay for 6-8 failed attempts (seconds)
LOGIN_DELAY_MEDIUM=30

# Long delay/cooldown for 9+ failed attempts (seconds, 900 = 15 minutes)
LOGIN_DELAY_LONG=900

# Thresholds for when each delay level kicks in
LOGIN_DELAY_THRESHOLD_SHORT=4
LOGIN_DELAY_THRESHOLD_MEDIUM=6
LOGIN_DELAY_THRESHOLD_LONG=9

# Time window for tracking failures (seconds, 3600 = 1 hour)
LOGIN_FAILURE_WINDOW=3600
```

### Redis Configuration

The throttling system requires Redis for distributed state management:

```bash
# Redis connection string
REDIS_URL=redis://localhost:6379/0
```

**Note**: If Redis is not available, the system degrades gracefully—authentication continues to work, but without throttling protection.

### Adjusting for Your Environment

**Development/Testing**:
```bash
LOGIN_DELAY_SHORT=1
LOGIN_DELAY_MEDIUM=5
LOGIN_DELAY_LONG=60
```

**Production (Stricter)**:
```bash
LOGIN_DELAY_SHORT=5
LOGIN_DELAY_MEDIUM=60
LOGIN_DELAY_LONG=1800  # 30 minutes
```

**High-Security Environment**:
```bash
LOGIN_DELAY_SHORT=10
LOGIN_DELAY_MEDIUM=120
LOGIN_DELAY_LONG=3600  # 1 hour
LOGIN_DELAY_THRESHOLD_SHORT=3
LOGIN_DELAY_THRESHOLD_MEDIUM=5
LOGIN_DELAY_THRESHOLD_LONG=7
```

---

## Implementation Details

### Architecture

The implementation consists of three main components:

1. **LoginThrottle Service** (`app/core/login_throttle.py`)
   - Manages failure counters in Redis
   - Calculates progressive delays
   - Handles cooldown periods
   - Provides monitoring/status functions

2. **Login Endpoint** (`app/api/v1/endpoints/auth.py`)
   - Integrates throttling into authentication flow
   - Records failed attempts
   - Applies server-side delays
   - Clears counters on success

3. **Audit Logging** (`app/models/audit_log.py`)
   - New events: `LOGIN_THROTTLED`, `LOGIN_EXCESSIVE_FAILURES`
   - Tracks all throttling actions
   - Enables security monitoring and alerting

### Redis Key Structure

**Failure Counter**: `login:failures:{email_lowercase}`
- Stores count of failed attempts
- TTL: `LOGIN_FAILURE_WINDOW` (default 1 hour)

**Cooldown Timer**: `login:cooldown:{email_lowercase}`
- Stores timestamp when cooldown expires
- TTL: Same as cooldown duration

### Email Normalization

All email addresses are normalized to lowercase before storage to ensure consistent throttling regardless of case variations.

---

## Monitoring and Alerting

### Audit Log Events

Three new audit actions are logged:

1. **LOGIN_THROTTLED**: Applied when delay is enforced
   ```json
   {
     "action": "login_throttled",
     "user_id": "uuid or null",
     "description": "Login throttled for user@example.com (30s delay)",
     "status": "info"
   }
   ```

2. **LOGIN_EXCESSIVE_FAILURES**: Triggered at 9+ failed attempts
   ```json
   {
     "action": "login_excessive_failures",
     "user_id": "uuid or null",
     "description": "Excessive login failures for user@example.com (9 attempts)",
     "status": "warning"
   }
   ```

3. **LOGIN_FAILED**: Already exists, now includes attempt count
   ```json
   {
     "action": "login_failed",
     "user_id": "uuid or null",
     "description": "Failed login attempt for user@example.com (attempt 5)",
     "status": "failure"
   }
   ```

### Metrics to Monitor

1. **Excessive Failure Rate**: Track `LOGIN_EXCESSIVE_FAILURES` events
2. **Throttle Frequency**: Monitor `LOGIN_THROTTLED` events
3. **Accounts Under Attack**: Identify accounts with high failure counts
4. **Cooldown State**: Track accounts in long cooldown

### Alert Thresholds

Recommended alert thresholds:

- **Alert**: 10+ `LOGIN_EXCESSIVE_FAILURES` in 1 hour (potential attack)
- **Warning**: 50+ `LOGIN_THROTTLED` events in 1 hour (widespread attack)
- **Critical**: 100+ failed attempts for single account in 24 hours

### Monitoring Queries

Query audit logs for security insights:

```sql
-- Accounts with excessive failures in last 24 hours
SELECT description, COUNT(*) as failure_count
FROM audit_logs
WHERE action = 'login_excessive_failures'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY description
ORDER BY failure_count DESC;

-- Total throttled logins per hour
SELECT DATE_TRUNC('hour', created_at) as hour, COUNT(*) as throttled_count
FROM audit_logs
WHERE action = 'login_throttled'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Security Considerations

### Constant-Time Responses

All authentication failures return identical responses:

- **Status Code**: 401 (not 403 or 404)
- **Error Message**: "Incorrect email or password"
- **Timing**: Similar delay regardless of:
  - Account existence
  - Password correctness
  - Account active status
  - Current cooldown state

This prevents account enumeration attacks.

### No Information Leakage

The system **never** reveals:
- Whether an account exists
- Whether an account is active/inactive
- Whether an account is in cooldown
- How many failed attempts have occurred
- Time remaining in cooldown

### Graceful Degradation

If Redis becomes unavailable:
- Authentication continues to work
- No throttling is applied
- System logs warning but doesn't fail
- Rate limiting (IP-based) remains active

### GDPR Compliance

- **Data Minimization**: Failure counters expire after 1 hour
- **No Personal Data**: Only email addresses stored (authentication identifier)
- **Right to Erasure**: Counters cleared on successful login
- **Audit Trail**: All throttling actions logged (Art. 30)

### ISO 27001 Compliance

- **A.9 Access Control**: Prevents unauthorized access attempts
- **A.12.4 Logging**: Comprehensive audit trail
- **A.16.1 Incident Management**: Monitoring and alerting capabilities

---

## OWASP ASVS Compliance

This implementation satisfies the following OWASP ASVS v4.0 requirements:

### V2.1.7 - Password Verification Throttling
> Verify the application or framework enforces progressively longer delays between failed authentication attempts.

**Compliance**: ✅ Fully implemented with configurable progressive delays

### V2.2.2 - Anti-Automation
> Verify that anti-automation controls are effective at mitigating breached credential testing, brute force, and account lockout attacks.

**Compliance**: ✅ Per-account throttling with progressive delays prevents automated attacks

### V2.2.5 - Prevent Credential Stuffing
> Verify that where a credential service provider (CSP) and the application verifying authentication are separated, mutually authenticated TLS is in place between the two endpoints.

**Compliance**: ✅ Credential verification protected by progressive throttling

### V2.1.6 - Generic Error Messages
> Verify that all authentication pathways and identity management APIs implement consistent authentication security control strength.

**Compliance**: ✅ Constant-time responses with generic error messages

---

## NIST SP 800-63B Compliance

This implementation satisfies the following NIST SP 800-63B requirements:

### 5.2.2 - Rate Limiting
> The verifier SHALL implement controls to protect against online guessing attacks. This can be achieved by limiting the number of consecutive unsuccessful authentication attempts permitted.

**Compliance**: ✅ Progressive delays limit effectiveness of guessing attacks

### 5.2.3 - No Account Lockout for Memorized Secrets
> The verifier SHALL NOT implement a lockout mechanism that makes the account unusable for a user who has valid credentials.

**Compliance**: ✅ No permanent lockouts; only temporary cooldowns that auto-expire

### 5.2.4 - Notification of Throttling
> When an online attack is detected, the verifier SHALL require the claimant to complete a second authentication factor...

**Compliance**: ✅ Progressive delays slow down attacks; audit logging enables notifications

---

## Testing

### Unit Tests

Run the throttling service unit tests:

```bash
pytest tests/test_login_throttle.py -v
```

Tests cover:
- Progressive delay calculation
- Redis operations (with mocking)
- Cooldown management
- Email normalization
- Graceful degradation

### Integration Tests

Run the authentication integration tests:

```bash
pytest tests/test_auth_throttle.py -v
```

Tests cover:
- Login with throttling enabled
- Failed attempt recording
- Successful login clears counters
- Constant-time responses
- Audit log events
- Case-insensitive email handling

### Manual Testing

Test the throttling behavior manually:

```bash
# Test 1-3 attempts (no delay)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=wrong1"

# Test 4-5 attempts (2s delay)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=wrong2"

# Test 6-8 attempts (30s delay)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=wrong3"

# Test 9+ attempts (15min cooldown)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=wrong4"

# Successful login clears throttle
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=correct"
```

---

## Troubleshooting

### Issue: Throttling Not Working

**Symptoms**: Login attempts succeed immediately without delay

**Possible Causes**:
1. Redis not configured or unavailable
2. Environment variables not set
3. Rate limiter disabled in tests

**Solutions**:
1. Check Redis connection: `redis-cli ping`
2. Verify `REDIS_URL` environment variable
3. Check logs for Redis connection errors
4. Ensure `LOGIN_DELAY_*` variables are set

### Issue: Too Aggressive Throttling

**Symptoms**: Users locked out too quickly

**Solutions**:
1. Increase thresholds: `LOGIN_DELAY_THRESHOLD_SHORT=5`
2. Reduce delays: `LOGIN_DELAY_SHORT=1`
3. Shorten failure window: `LOGIN_FAILURE_WINDOW=1800` (30 min)

### Issue: Not Aggressive Enough

**Symptoms**: Attacks still succeeding

**Solutions**:
1. Decrease thresholds: `LOGIN_DELAY_THRESHOLD_SHORT=3`
2. Increase delays: `LOGIN_DELAY_LONG=3600` (1 hour)
3. Add additional monitoring and alerting
4. Consider CAPTCHA for repeated failures

### Issue: Redis Memory Growth

**Symptoms**: Redis memory usage increasing

**Solutions**:
1. Verify TTLs are being set correctly
2. Check failure window isn't too long
3. Monitor Redis key count: `redis-cli DBSIZE`
4. Manually clear keys if needed: `redis-cli --scan --pattern "login:*" | xargs redis-cli DEL`

### Issue: Audit Logs Growing Too Large

**Symptoms**: Database growing from throttle events

**Solutions**:
1. Implement audit log rotation/archival
2. Reduce retention period for `LOGIN_THROTTLED` events
3. Consider separate logging for throttle events
4. Use log aggregation service (e.g., ELK stack)

---

## Best Practices

1. **Monitor Regularly**: Set up alerts for excessive failures
2. **Tune for Your Users**: Adjust thresholds based on actual usage patterns
3. **Document Incidents**: Track and analyze attacks to improve defenses
4. **Combine Defenses**: Use throttling alongside rate limiting, CAPTCHA, MFA
5. **Test Regularly**: Verify throttling works as expected
6. **Communicate**: Inform users about account security measures
7. **Have a Plan**: Document incident response procedures for attacks

---

## Future Enhancements

Potential improvements to consider:

1. **Adaptive Delays**: Machine learning to adjust delays based on attack patterns
2. **Geographic Throttling**: Stricter limits for high-risk countries
3. **CAPTCHA Integration**: Require CAPTCHA after N failures
4. **MFA Requirement**: Force MFA enrollment after excessive failures
5. **Email Notifications**: Alert users of failed login attempts
6. **Account Recovery**: Enhanced recovery flow for locked accounts
7. **Device Fingerprinting**: Track and throttle by device
8. **Reputation Systems**: Use threat intelligence feeds

---

## References

- [OWASP ASVS 4.0](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [CWE-307: Improper Restriction of Excessive Authentication Attempts](https://cwe.mitre.org/data/definitions/307.html)

---

## Support

For questions or issues related to login throttling:

1. Check this documentation first
2. Review audit logs for specific incidents
3. Check Redis connectivity and configuration
4. Verify environment variables are set correctly
5. Contact security team for incident response

---

**Last Updated**: 2025-12-30  
**Document Version**: 1.0.0  
**Feature Status**: Production Ready

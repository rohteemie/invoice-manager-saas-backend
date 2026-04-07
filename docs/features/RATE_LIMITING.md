# Rate Limiting Documentation

## Overview

Rate limiting protects the Multi-Tenant SaaS Backend from abuse, ensures fair resource allocation across tenants, and maintains API stability under high load.

The system implements **tiered rate limiting** based on user roles and operation types, with configurable limits and exemptions for superadmin users and specific IPs.

## Implementation

**Technology**: SlowAPI (FastAPI rate limiting extension)  
**Storage**: Redis (distributed rate limiting)  
**Fallback**: In-memory storage (single instance)

## Architecture

### Components

1. **Rate Limiter**: SlowAPI integration (`app/core/rate_limit.py`)
2. **Redis Backend**: Distributed rate limit storage
3. **Custom Key Function**: Per-user/IP rate limiting with exemptions
4. **Error Handler**: Custom 429 responses with rate limit headers
5. **Rate Limit Middleware**: Adds informational headers to all responses

### How It Works

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Check Exemptions │ (Superadmin/IP)
└──────┬───────────┘
       │
       ▼
    ┌──┴────┐
    │Exempt?│
    └──┬────┘
       │
   ┌───┴────┐
   │  Yes   │ No
   │        │
   ▼        ▼
┌──────┐ ┌──────────────────┐
│Allow │ │ Identify Client  │ (User ID/Role or IP)
└──────┘ └──────┬───────────┘
                │
                ▼
         ┌──────────────────┐
         │ Determine Limit  │ (Role-based or Operation-based)
         └──────┬───────────┘
                │
                ▼
         ┌──────────────────┐
         │ Check Redis      │ (Request count)
         └──────┬───────────┘
                │
                ▼
            ┌───┴────┐
            │Allowed?│
            └───┬────┘
                │
            ┌───┴────┐
            │  Yes   │ No
            │        │
            ▼        ▼
         ┌──────┐ ┌──────┐
         │Allow │ │ 429  │
         └──────┘ └──────┘
```

## Configuration

### Environment Variables

```bash
# Redis URL for distributed rate limiting
REDIS_URL=redis://localhost:6379/0

# Tiered Rate Limits by User Role
RATE_LIMIT_UNAUTHENTICATED=20/minute    # Unauthenticated users
RATE_LIMIT_ATTENDANT=100/minute         # ATTENDANT role
RATE_LIMIT_MANAGER=200/minute           # MANAGER role  
RATE_LIMIT_ADMIN=500/minute             # ADMIN role
RATE_LIMIT_OWNER=1000/minute            # OWNER role
# Superadmin users are exempt from rate limiting

# Operation-Type Multipliers
RATE_LIMIT_READ_MULTIPLIER=2.0          # Read ops get 2x base limit
RATE_LIMIT_WRITE_MULTIPLIER=1.0         # Write ops use base limit

# IP Exemptions (comma-separated)
RATE_LIMIT_EXEMPT_IPS=192.168.1.1,10.0.0.1

# Retry-After fallback in seconds
RATE_LIMIT_RETRY_AFTER_FALLBACK=60
```

### Rate Limit Strategy

**Fixed Window**: Limits reset at fixed intervals

- Simple and predictable
- May allow bursts at window boundaries
- Good for most use cases

## Rate Limits

### Role-Based Limits

The system applies different rate limits based on user roles:

| User Type | Base Limit | Description |
|-----------|------------|-------------|
| Unauthenticated | 20/minute | Anonymous/Guest users |
| ATTENDANT | 100/minute | Basic authenticated users |
| MANAGER | 200/minute | Manager role users |
| ADMIN | 500/minute | Administrator role users |
| OWNER | 1000/minute | Tenant owner users |
| Superadmin | Unlimited | Platform superadmin (exempt) |

### Operation-Based Limits

Different operations have different rate limits via multipliers:

| Operation Type | Multiplier | Example (ATTENDANT) |
|----------------|------------|---------------------|
| Read (GET) | 2.0x | 200/minute |
| Write (POST/PUT/DELETE) | 1.0x | 100/minute |

### Endpoint-Specific Limits

Authentication endpoints have strict limits regardless of role:

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/api/v1/auth/register` | 5/minute | Prevent spam registrations |
| `/api/v1/auth/login` | 10/minute | Prevent brute force attacks |
| `/api/v1/auth/refresh` | 20/minute | Allow frequent token refresh |
| `/api/v1/auth/forgot-password` | 3/hour | Prevent abuse |
| `/api/v1/auth/reset-password` | 3/hour | Prevent abuse |
| `/api/v1/auth/verify-email` | 5/hour | Email verification |

### Customization

Limits can be applied via decorators or dynamic functions:

```python
from app.core.rate_limit import limiter, get_role_based_limit, get_read_limit, get_write_limit

# Static limit
@router.post("/sensitive-operation")
@limiter.limit("5/minute")
def sensitive_operation(request: Request):
    pass

# Role-based dynamic limit
@router.get("/data")
@limiter.limit(get_role_based_limit)
def get_data(request: Request):
    pass

# Read operation limit (applies 2x multiplier)
@router.get("/invoices")
@limiter.limit(get_read_limit)
def list_invoices(request: Request):
    pass

# Write operation limit (applies 1x multiplier)
@router.post("/invoices")
@limiter.limit(get_write_limit)
def create_invoice(request: Request):
    pass
```

## User Identification

### Exemptions

The following users/IPs are **exempt** from rate limiting:

1. **Superadmin Users**: Users with `is_superadmin=True` flag
2. **Exempt IPs**: IPs listed in `RATE_LIMIT_EXEMPT_IPS` environment variable

```python
def get_user_identifier(request: Request) -> str:
    # Check if IP is exempt
    if is_ip_exempt(client_ip):
        return None  # Unlimited
    
    # Check if user is superadmin
    user = getattr(request.state, "user", None)
    if user and user.is_superadmin:
        return None  # Unlimited
    
    # Otherwise return user ID or IP
    return f"user:{user.id}" if user else client_ip
```

### Authenticated Users

Rate limits are applied per **user ID** based on their role:

```python
def get_user_identifier(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"
    return get_remote_address(request)
```

### Unauthenticated Users

Rate limits are applied per **IP address**:

```python
return get_remote_address(request)  # Client IP
```

### Behind Proxy/Load Balancer

Use `X-Forwarded-For` header:

```python
def get_remote_address(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host
```

## Error Responses

### 429 Too Many Requests

**Response Structure**:

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "detail": "Retry in 45 seconds"
}
```

**Headers**:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 45
```

### Rate Limit Headers

All responses include informational rate limit headers:

- **X-RateLimit-Limit**: Maximum requests allowed in the current window
- **X-RateLimit-Remaining**: Requests remaining (only in 429 responses)
- **X-RateLimit-Reset**: Seconds until rate limit resets

These headers help clients implement backoff strategies and display limits to users.

### Custom Error Handler

```python
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail)
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": limit_value,
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after)
        }
    )
```

## Redis Configuration

### Setup

```bash
# Install Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or use managed Redis
# - AWS ElastiCache
# - Google Cloud Memorystore
# - Azure Cache for Redis
```

### Connection

```python
# app/core/rate_limit.py
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=settings.REDIS_URL,  # redis://localhost:6379/0
    strategy="fixed-window"
)
```

### Fallback to In-Memory

If Redis is unavailable:

```python
if redis_client:
    # Use Redis
    limiter = Limiter(
        key_func=get_user_identifier,
        storage_uri=settings.REDIS_URL
    )
else:
    # Fall back to in-memory
    limiter = Limiter(
        key_func=get_user_identifier,
        default_limits=["100/minute"]
    )
```

## Testing

### Disable in Tests

Rate limiting is automatically disabled in tests:

```python
# tests/conftest.py
@pytest.fixture(scope="function", autouse=True)
def disable_rate_limit():
    from app.core.rate_limit import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True
```

### Manual Testing

Test rate limits with curl:

```bash
# Test role-based limits - Unauthenticated user (20/minute)
for i in {1..25}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -d "username=test@example.com" \
    -d "password=test123" \
    -i | grep "HTTP"
done

# Expected output:
# HTTP/1.1 401 (first 20 requests)
# HTTP/1.1 429 (requests 21-25)

# Test with authenticated user (higher limits based on role)
TOKEN="your-jwt-token"
for i in {1..150}; do
  curl -X GET http://localhost:8000/api/v1/invoices/ \
    -H "Authorization: Bearer $TOKEN" \
    -i | grep "HTTP"
done

# Test rate limit headers
curl -v http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  | grep "X-RateLimit"
# Should show: X-RateLimit-Limit, X-RateLimit-Reset
```

### Testing Role-Based Limits

```bash
# Test as ATTENDANT (100/minute base, 200/minute for reads)
# Test as MANAGER (200/minute base, 400/minute for reads)
# Test as ADMIN (500/minute base, 1000/minute for reads)
# Test as OWNER (1000/minute base, 2000/minute for reads)
# Test as Superadmin (unlimited)
```

### Load Testing

Use Apache Bench or similar:

```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/invoices/

# Check how many hit rate limit
```

## Monitoring

### Metrics

Track rate limit events:

```python
from app.core.metrics import rate_limit_hits

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request):
    try:
        # Login logic
    except RateLimitExceeded:
        rate_limit_hits.labels(endpoint="/login").inc()
        raise
```

### Logs

Rate limit events are logged:

```
WARNING - slowapi - ratelimit 10 per 1 minute (user:123) exceeded at endpoint: /api/v1/auth/login
```

### Dashboards

Monitor rate limit usage:

```promql
# Rate limit hit rate
rate(rate_limit_hits_total[5m])

# Top rate-limited endpoints
topk(5, rate_limit_hits_total)
```

## Advanced Configuration

### Role-Based Limits (Built-in)

The system includes built-in role-based rate limiting:

```python
from app.core.rate_limit import get_role_based_limit, get_read_limit, get_write_limit

# Use role-based limit
@router.get("/data")
@limiter.limit(get_role_based_limit)
def get_data(request: Request):
    pass

# Use read limit (2x role-based limit)
@router.get("/invoices")
@limiter.limit(get_read_limit)
def list_invoices(request: Request):
    pass

# Use write limit (1x role-based limit)
@router.post("/invoices")
@limiter.limit(get_write_limit)
def create_invoice(request: Request):
    pass
```

### IP Exemptions (Built-in)

Configure exempt IPs via environment variable:

```bash
# In .env file
RATE_LIMIT_EXEMPT_IPS=192.168.1.1,10.0.0.1,172.16.0.1
```

The system automatically exempts these IPs from all rate limiting.

### Superadmin Exemption (Built-in)

Users with `is_superadmin=True` are automatically exempt from all rate limits.

```python
# Superadmin users bypass rate limiting
user.is_superadmin = True  # This user has unlimited access
```

### Per-Tenant Limits (Custom Extension)

Implement custom limits per tenant if needed:

```python
def get_tenant_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        tenant = get_tenant(user.tenant_id)
        return tenant.rate_limit or get_role_based_limit(request)
    return settings.RATE_LIMIT_UNAUTHENTICATED

@router.post("/endpoint")
@limiter.limit(get_tenant_limit)
def endpoint(request: Request):
    pass
```

### Dynamic Limits Based on Plans (Custom Extension)

Adjust limits based on subscription plans:

```python
PLAN_LIMITS = {
    "free": "50/minute",
    "pro": "200/minute",
    "enterprise": "1000/minute"
}

def get_plan_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        plan = get_user_plan(user.id)
        return PLAN_LIMITS.get(plan, get_role_based_limit(request))
    return settings.RATE_LIMIT_UNAUTHENTICATED
```

## Best Practices

### 1. Set Appropriate Limits

- **Too Low**: Users frustrated, legitimate requests blocked
- **Too High**: No protection from abuse
- **Just Right**: Balance security and usability

### 2. Different Limits for Different Operations

✅ **Built-in**: The system provides read/write multipliers

- **Read Operations (GET)**: 2x base limit via `get_read_limit()`
- **Write Operations (POST/PUT/DELETE)**: 1x base limit via `get_write_limit()`
- **Expensive Operations**: Use static limits like `"5/minute"`
- **Authentication**: Static limits (5-20/minute) to prevent brute force

### 3. Use Redis for Production

- In-memory storage not suitable for multi-instance deployments
- Redis provides distributed rate limiting
- Persist limits across restarts

### 4. Provide Clear Error Messages

```json
{
  "error": "Rate limit exceeded",
  "message": "You've made too many requests. Please wait 30 seconds.",
  "detail": "Limit: 10 requests per minute",
  "retry_after": 30
}
```

### 5. Log Rate Limit Events

For security auditing and capacity planning:

```python
logger.warning(
    f"Rate limit exceeded for user {user.id}",
    extra={
        "user_id": user.id,
        "endpoint": request.url.path,
        "ip": client_ip
    }
)
```

## Troubleshooting

### Rate Limits Not Working

1. **Check Redis Connection**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Verify Middleware**:
   ```python
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
   ```

3. **Check Decorator**:
   ```python
   @limiter.limit("10/minute")  # Correct
   # vs
   @limiter.limit(10/minute)   # Wrong (syntax error)
   ```

### Users Hitting Limits Unexpectedly

1. **Check User Identification**: Ensure users are identified correctly
2. **Review Limit Values**: May be too restrictive
3. **Check Time Windows**: Ensure window size is appropriate
4. **Monitor Patterns**: Use logs to understand usage

### Redis Connection Issues

1. **Connection String**: Verify `REDIS_URL` format
2. **Network Access**: Ensure Redis is accessible
3. **Fallback**: System should work without Redis (in-memory)

## Security Considerations

### 1. Rate Limit Bypass Prevention

- **Don't Trust Client IP Alone**: Use authenticated user ID
- **Validate X-Forwarded-For**: Prevent header manipulation
- **Use Redis**: Prevent per-instance bypass

### 2. DDoS Protection

Rate limiting is one layer:

- **Use CDN**: Cloudflare, Akamai for DDoS protection
- **WAF**: Web Application Firewall for advanced filtering
- **Rate Limiting**: API-level protection

### 3. Audit Logging

Log all rate limit violations:

```python
logger.warning(
    "Rate limit exceeded",
    extra={
        "user_id": user.id if user else None,
        "ip": client_ip,
        "endpoint": request.url.path,
        "method": request.method
    }
)
```

## Integration Examples

### Nginx Rate Limiting

Combine with Nginx for multi-layer protection:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=50r/m;

location /api/ {
    limit_req zone=api burst=10 nodelay;
    proxy_pass http://backend;
}
```

### Kubernetes

Use network policies:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: rate-limit-policy
spec:
  podSelector:
    matchLabels:
      app: multi-tenant-saas
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
```

---

## Summary of Tiered Rate Limiting Features

### ✅ Implemented Features

1. **Role-Based Rate Limiting**
   - Unauthenticated: 20/minute
   - ATTENDANT: 100/minute
   - MANAGER: 200/minute
   - ADMIN: 500/minute
   - OWNER: 1000/minute
   - Superadmin: Unlimited (exempt)

2. **Operation-Based Limits**
   - Read operations (GET): 2x base rate limit
   - Write operations (POST/PUT/DELETE): 1x base rate limit
   - Configurable via `RATE_LIMIT_READ_MULTIPLIER` and `RATE_LIMIT_WRITE_MULTIPLIER`

3. **IP Exemptions**
   - Configurable via `RATE_LIMIT_EXEMPT_IPS` environment variable
   - Comma-separated list of exempt IP addresses
   - Exempt IPs get unlimited access

4. **Superadmin Exemptions**
   - Users with `is_superadmin=True` are automatically exempt
   - Bypass all rate limiting restrictions

5. **Rate Limit Headers**
   - `X-RateLimit-Limit`: Maximum requests allowed
   - `X-RateLimit-Remaining`: Requests remaining (in 429 responses)
   - `X-RateLimit-Reset`: Seconds until limit resets
   - `Retry-After`: Standard retry header

6. **Configuration via Environment Variables**
   - All rate limits configurable without code changes
   - Easy to adjust limits per environment
   - Defaults provided for all settings

### 📝 Configuration Quick Reference

```bash
# .env file
RATE_LIMIT_UNAUTHENTICATED=20/minute
RATE_LIMIT_ATTENDANT=100/minute
RATE_LIMIT_MANAGER=200/minute
RATE_LIMIT_ADMIN=500/minute
RATE_LIMIT_OWNER=1000/minute
RATE_LIMIT_READ_MULTIPLIER=2.0
RATE_LIMIT_WRITE_MULTIPLIER=1.0
RATE_LIMIT_EXEMPT_IPS=192.168.1.1,10.0.0.1
```

### 🔧 Usage Examples

```python
# Static limit
@limiter.limit("5/minute")

# Role-based dynamic limit
@limiter.limit(get_role_based_limit)

# Read operation (2x base)
@limiter.limit(get_read_limit)

# Write operation (1x base)
@limiter.limit(get_write_limit)
```

---

**Last Updated**: Phase 5 - Tiered Rate Limiting Implementation  
**Version**: 2.0.0  
**Status**: ✅ Active

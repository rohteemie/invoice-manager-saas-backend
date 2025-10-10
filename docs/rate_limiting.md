# Rate Limiting Documentation

## Overview

Rate limiting protects the Multi-Tenant SaaS Backend from abuse, ensures fair resource allocation across tenants, and maintains API stability under high load.

## Implementation

**Technology**: SlowAPI (FastAPI rate limiting extension)  
**Storage**: Redis (distributed rate limiting)  
**Fallback**: In-memory storage (single instance)

## Architecture

### Components

1. **Rate Limiter**: SlowAPI integration (`app/core/rate_limit.py`)
2. **Redis Backend**: Distributed rate limit storage
3. **Custom Key Function**: Per-user/IP rate limiting
4. **Error Handler**: Custom 429 responses

### How It Works

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Identify Client  │ (User ID or IP)
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

# Default rate limits (optional)
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=20/minute
```

### Rate Limit Strategy

**Fixed Window**: Limits reset at fixed intervals

- Simple and predictable
- May allow bursts at window boundaries
- Good for most use cases

## Rate Limits

### Endpoint-Specific Limits

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/api/v1/auth/register` | 5/minute | Prevent spam registrations |
| `/api/v1/auth/login` | 10/minute | Prevent brute force attacks |
| `/api/v1/auth/refresh` | 20/minute | Allow frequent token refresh |
| Protected endpoints | 100/minute | General API usage |
| Public endpoints | 20/minute | Unauthenticated access |

### Customization

Limits are applied via decorators:

```python
from app.core.rate_limit import limiter

@router.post("/sensitive-operation")
@limiter.limit("5/minute")
def sensitive_operation(request: Request):
    # Operation logic
    pass
```

## User Identification

### Authenticated Users

Rate limits are applied per **user ID**:

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
```

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
            "Retry-After": "60"
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
# Make 15 rapid requests (limit is 10/minute)
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -d "username=test@example.com" \
    -d "password=test123" \
    -i | grep "HTTP"
done

# Expected output:
# HTTP/1.1 401 (first 10 requests)
# HTTP/1.1 429 (requests 11-15)
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

### Per-Tenant Limits

Implement custom limits per tenant:

```python
def get_tenant_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        tenant = get_tenant(user.tenant_id)
        return tenant.rate_limit or "100/minute"
    return "20/minute"

@router.post("/endpoint")
@limiter.limit(get_tenant_limit)
def endpoint(request: Request):
    pass
```

### Dynamic Limits

Adjust limits based on plan:

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
        return PLAN_LIMITS.get(plan, "50/minute")
    return "20/minute"
```

### Exemptions

Exempt certain users or IPs:

```python
def get_user_identifier(request: Request) -> str:
    # Exempt admin users
    user = getattr(request.state, "user", None)
    if user and user.role == UserRole.OWNER:
        return None  # No rate limit
    
    # Exempt internal IPs
    client_ip = get_remote_address(request)
    if client_ip in ["10.0.0.0/8", "192.168.0.0/16"]:
        return None
    
    return f"user:{user.id}" if user else client_ip
```

## Best Practices

### 1. Set Appropriate Limits

- **Too Low**: Users frustrated, legitimate requests blocked
- **Too High**: No protection from abuse
- **Just Right**: Balance security and usability

### 2. Different Limits for Different Operations

- **Expensive Operations**: Lower limits (e.g., 5/minute)
- **Reads**: Higher limits (e.g., 100/minute)
- **Authentication**: Medium limits (e.g., 10/minute)

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

**Last Updated**: Phase 4 - Sprint 4.4  
**Version**: 1.0.0  
**Status**: ✅ Active

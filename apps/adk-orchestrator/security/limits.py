from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Optional

def limiter_key_func(request: Request) -> str:
    """
    Rate limiter key function that uses tenant_id if available,
    otherwise falls back to client IP.
    """
    # Try to get tenant_id from request state (set by rate_limit_context)
    tenant_id = getattr(request.state, 'tenant_id', None)
    if tenant_id:
        return f"tenant:{tenant_id}"
    
    # Fallback to client IP
    return get_remote_address(request)

# Create limiter instance with custom key function
limiter = Limiter(key_func=limiter_key_func)

def rate_limit_context(request: Request, tenant_id: Optional[str] = None) -> None:
    """
    Set request.state.tenant_id from Principal for rate limiting.
    This should be called in middleware or dependency injection.
    """
    if tenant_id:
        request.state.tenant_id = tenant_id

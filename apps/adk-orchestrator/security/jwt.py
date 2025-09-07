import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import Principal, TenantContext


# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "kyros-dev"
JWT_AUDIENCE = "kyros-api"

# FastAPI security scheme
security = HTTPBearer()


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"verify_exp": True, "verify_iat": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_principal(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
    """FastAPI dependency to extract and validate the principal from JWT token."""
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    # Extract required fields from JWT payload
    sub = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    scopes = payload.get("scopes", [])
    
    if not sub or not tenant_id:
        raise HTTPException(status_code=401, detail="Missing required token claims")
    
    return Principal(sub=sub, tenant_id=tenant_id, scopes=scopes)


def get_tenant(principal: Principal = Depends(get_principal)) -> TenantContext:
    """FastAPI dependency to get tenant context from principal."""
    # In a real implementation, this would fetch tenant config from a database
    # For now, we'll use default values based on the tenant_id
    return TenantContext(
        id=principal.tenant_id,
        rate_limit_rps=5,  # Default rate limit
        model_caps={}  # Default empty model caps
    )


def create_dev_token(sub: str, tenant_id: str, scopes: list = None, expires_in_hours: int = 1) -> str:
    """Create a development JWT token for testing."""
    if scopes is None:
        scopes = []
    
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "scopes": scopes,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(hours=expires_in_hours)
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

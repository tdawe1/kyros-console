from pydantic import BaseModel
from typing import List, Dict, Any


class Principal(BaseModel):
    """Represents an authenticated user principal."""
    sub: str  # Subject identifier (user ID)
    tenant_id: str  # Tenant identifier
    scopes: List[str] = []  # Authorization scopes


class TenantContext(BaseModel):
    """Represents tenant-specific configuration and context."""
    id: str  # Tenant identifier
    rate_limit_rps: int  # Rate limit in requests per second
    model_caps: Dict[str, Any] = {}  # Model capabilities/restrictions

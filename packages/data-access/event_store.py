from abc import ABC, abstractmethod
from typing import Iterable, Optional

class EventStore(ABC):
    @abstractmethod
    async def append(self, stream_id: str, events: list[dict], expected_version: int|None=None): ...
    @abstractmethod
    async def read(self, stream_id: str, from_version: int=0) -> Iterable[dict]: ...
    
    def _get_tenant_scoped_stream(self, base_stream: str, tenant_id: Optional[str] = None) -> str:
        """Generate tenant-scoped stream name.
        
        Args:
            base_stream: Base stream name (e.g., "runs", "tasks")
            tenant_id: Tenant identifier, None for public streams
            
        Returns:
            Tenant-scoped stream name (e.g., "runs-tenant123" or "runs-public")
        """
        if tenant_id is None:
            return f"{base_stream}-public"
        return f"{base_stream}-{tenant_id}"
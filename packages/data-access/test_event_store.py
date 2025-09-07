import pytest
from event_store import EventStore


class MockEventStore(EventStore):
    """Mock implementation of EventStore for testing."""
    
    def __init__(self):
        self.events = {}
        self.versions = {}
    
    async def append(self, stream_id: str, events: list[dict], expected_version: int|None=None):
        if stream_id not in self.events:
            self.events[stream_id] = []
            self.versions[stream_id] = -1
        
        if expected_version is not None and self.versions[stream_id] != expected_version:
            raise ValueError(f"Expected version {expected_version}, got {self.versions[stream_id]}")
        
        self.events[stream_id].extend(events)
        self.versions[stream_id] += len(events)
    
    async def read(self, stream_id: str, from_version: int=0):
        if stream_id not in self.events:
            return []
        return self.events[stream_id][from_version:]


class TestEventStoreTenantScoping:
    """Test cases for EventStore tenant scoping functionality."""
    
    def test_get_tenant_scoped_stream_with_tenant_id(self):
        """Test tenant-scoped stream name generation with tenant ID."""
        event_store = MockEventStore()
        
        # Test with tenant ID
        stream_name = event_store._get_tenant_scoped_stream("runs", "tenant123")
        assert stream_name == "runs-tenant123"
        
        # Test with different tenant ID
        stream_name = event_store._get_tenant_scoped_stream("tasks", "tenant456")
        assert stream_name == "tasks-tenant456"
    
    def test_get_tenant_scoped_stream_without_tenant_id(self):
        """Test tenant-scoped stream name generation without tenant ID (public)."""
        event_store = MockEventStore()
        
        # Test with None tenant ID
        stream_name = event_store._get_tenant_scoped_stream("runs", None)
        assert stream_name == "runs-public"
        
        # Test with empty string tenant ID
        stream_name = event_store._get_tenant_scoped_stream("tasks", "")
        assert stream_name == "tasks-"
    
    def test_get_tenant_scoped_stream_different_base_streams(self):
        """Test tenant-scoped stream name generation with different base streams."""
        event_store = MockEventStore()
        
        # Test various base streams
        assert event_store._get_tenant_scoped_stream("audit", "tenant123") == "audit-tenant123"
        assert event_store._get_tenant_scoped_stream("locks", "tenant123") == "locks-tenant123"
        assert event_store._get_tenant_scoped_stream("agents", "tenant123") == "agents-tenant123"
    
    @pytest.mark.asyncio
    async def test_tenant_scoped_streams_are_isolated(self):
        """Test that different tenant streams are isolated."""
        event_store = MockEventStore()
        
        # Create events for different tenants
        tenant1_stream = event_store._get_tenant_scoped_stream("runs", "tenant1")
        tenant2_stream = event_store._get_tenant_scoped_stream("runs", "tenant2")
        
        # Add events to tenant1 stream
        await event_store.append(tenant1_stream, [{"event": "run1"}, {"event": "run2"}])
        
        # Add events to tenant2 stream
        await event_store.append(tenant2_stream, [{"event": "run3"}])
        
        # Verify streams are isolated
        tenant1_events = list(await event_store.read(tenant1_stream))
        tenant2_events = list(await event_store.read(tenant2_stream))
        
        assert len(tenant1_events) == 2
        assert len(tenant2_events) == 1
        assert tenant1_events[0]["event"] == "run1"
        assert tenant2_events[0]["event"] == "run3"
    
    @pytest.mark.asyncio
    async def test_public_stream_isolation(self):
        """Test that public streams are isolated from tenant streams."""
        event_store = MockEventStore()
        
        # Create public and tenant streams
        public_stream = event_store._get_tenant_scoped_stream("runs", None)
        tenant_stream = event_store._get_tenant_scoped_stream("runs", "tenant1")
        
        # Add events to both streams
        await event_store.append(public_stream, [{"event": "public_run"}])
        await event_store.append(tenant_stream, [{"event": "tenant_run"}])
        
        # Verify streams are isolated
        public_events = list(await event_store.read(public_stream))
        tenant_events = list(await event_store.read(tenant_stream))
        
        assert len(public_events) == 1
        assert len(tenant_events) == 1
        assert public_events[0]["event"] == "public_run"
        assert tenant_events[0]["event"] == "tenant_run"


if __name__ == "__main__":
    pytest.main([__file__])

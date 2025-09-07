import json
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from audit.logger import audit, configure_event_store, AuditEvents
from security.models import Principal, TenantContext


class TestAuditLogger:
    """Test cases for the audit logger functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the global event store
        configure_event_store(None)
    
    def test_audit_logs_structured_json(self, caplog):
        """Test that audit function logs structured JSON with correct fields."""
        # Arrange
        principal = Principal(sub="user123", tenant_id="tenant456", scopes=[])
        tenant = TenantContext(id="tenant456", rate_limit_rps=10)
        event_name = "audit.test_event"
        data = {"key": "value", "number": 42}
        
        # Act
        asyncio.run(audit(event_name, principal, tenant, data))
        
        # Assert
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        
        # Parse the JSON log message
        log_data = json.loads(log_record.message)
        
        # Verify required fields
        assert "ts" in log_data
        assert "event" in log_data
        assert "actor" in log_data
        assert "tenant_id" in log_data
        assert "data" in log_data
        
        # Verify field values
        assert log_data["event"] == event_name
        assert log_data["actor"] == "user123"
        assert log_data["tenant_id"] == "tenant456"
        assert log_data["data"] == data
        
        # Verify timestamp format (ISO format with Z)
        assert log_data["ts"].endswith("Z")
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(log_data["ts"].replace("Z", "+00:00"))
    
    def test_audit_with_event_store_success(self):
        """Test that audit function works with EventStore configured."""
        # Arrange
        mock_event_store = Mock()
        mock_event_store._get_tenant_scoped_stream = Mock(return_value="audit-tenant123")
        mock_event_store.append = AsyncMock()
        
        configure_event_store(mock_event_store)
        
        principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
        tenant = TenantContext(id="tenant123", rate_limit_rps=10)
        event_name = "audit.test_event"
        data = {"test": "data"}
        
        # Act
        asyncio.run(audit(event_name, principal, tenant, data))
        
        # Assert
        mock_event_store._get_tenant_scoped_stream.assert_called_once_with("audit", "tenant123")
        mock_event_store.append.assert_called_once()
        
        # Verify the event structure passed to EventStore
        call_args = mock_event_store.append.call_args
        stream_name, events = call_args[0]
        assert stream_name == "audit-tenant123"
        assert len(events) == 1
        
        event = events[0]
        assert event["event_type"] == event_name
        assert event["actor"] == "user123"
        assert event["tenant_id"] == "tenant123"
        assert event["data"] == data
        assert "timestamp" in event
    
    def test_audit_with_event_store_failure_continues(self, caplog):
        """Test that audit continues to work even if EventStore fails."""
        # Arrange
        mock_event_store = Mock()
        mock_event_store._get_tenant_scoped_stream = Mock(side_effect=Exception("EventStore error"))
        mock_event_store.append = AsyncMock()
        
        configure_event_store(mock_event_store)
        
        principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
        tenant = TenantContext(id="tenant123", rate_limit_rps=10)
        event_name = "audit.test_event"
        data = {"test": "data"}
        
        # Act
        asyncio.run(audit(event_name, principal, tenant, data))
        
        # Assert - should still log successfully
        assert len(caplog.records) == 2  # One for the audit, one for the error
        log_record = caplog.records[0]
        log_data = json.loads(log_record.message)
        assert log_data["event"] == event_name
        
        # Check error was logged
        error_record = caplog.records[1]
        assert "Failed to append audit event to EventStore" in error_record.message
    
    def test_audit_without_event_store(self, caplog):
        """Test that audit works without EventStore configured."""
        # Arrange
        principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
        tenant = TenantContext(id="tenant123", rate_limit_rps=10)
        event_name = "audit.test_event"
        data = {"test": "data"}
        
        # Act
        asyncio.run(audit(event_name, principal, tenant, data))
        
        # Assert - should only log, no EventStore calls
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        log_data = json.loads(log_record.message)
        assert log_data["event"] == event_name
    
    def test_audit_events_constants(self):
        """Test that AuditEvents constants are defined correctly."""
        assert AuditEvents.PLAN_REQUESTED == "audit.plan_requested"
        assert AuditEvents.PLAN_STARTED == "audit.plan_started"
        assert AuditEvents.PLAN_FAILED == "audit.plan_failed"
        assert AuditEvents.PLAN_COMPLETED == "audit.plan_completed"
    
    def test_audit_with_complex_data(self, caplog):
        """Test that audit handles complex data structures."""
        # Arrange
        principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
        tenant = TenantContext(id="tenant123", rate_limit_rps=10)
        event_name = "audit.complex_event"
        data = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "boolean": True,
            "null_value": None,
            "unicode": "测试"
        }
        
        # Act
        asyncio.run(audit(event_name, principal, tenant, data))
        
        # Assert
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        log_data = json.loads(log_record.message)
        assert log_data["data"] == data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])

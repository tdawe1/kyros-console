#!/usr/bin/env python3
"""Simple manual test for audit logger functionality."""

import asyncio
from unittest.mock import Mock, AsyncMock
from audit.logger import audit, configure_event_store, AuditEvents
from security.models import Principal, TenantContext


def test_audit_basic():
    """Test basic audit functionality."""
    print("Testing basic audit functionality...")
    
    principal = Principal(sub="user123", tenant_id="tenant456", scopes=[])
    tenant = TenantContext(id="tenant456", rate_limit_rps=10)
    event_name = "audit.test_event"
    data = {"key": "value", "number": 42}
    
    # This should not raise an exception
    asyncio.run(audit(event_name, principal, tenant, data))
    print("✓ Basic audit test passed")


def test_audit_with_event_store():
    """Test audit with EventStore."""
    print("Testing audit with EventStore...")
    
    mock_event_store = Mock()
    mock_event_store._get_tenant_scoped_stream = Mock(return_value="audit-tenant123")
    mock_event_store.append = AsyncMock()
    
    configure_event_store(mock_event_store)
    
    principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
    tenant = TenantContext(id="tenant123", rate_limit_rps=10)
    event_name = "audit.test_event"
    data = {"test": "data"}
    
    asyncio.run(audit(event_name, principal, tenant, data))
    
    # Verify EventStore calls
    mock_event_store._get_tenant_scoped_stream.assert_called_once_with("audit", "tenant123")
    mock_event_store.append.assert_called_once()
    
    # Verify event structure
    call_args = mock_event_store.append.call_args
    stream_name, events = call_args[0]
    assert stream_name == "audit-tenant123"
    assert len(events) == 1
    
    event = events[0]
    assert event["event_type"] == event_name
    assert event["actor"] == "user123"
    assert event["tenant_id"] == "tenant123"
    assert event["data"] == data
    
    print("✓ EventStore audit test passed")


def test_audit_without_event_store():
    """Test audit without EventStore."""
    print("Testing audit without EventStore...")
    
    # Reset event store
    configure_event_store(None)
    
    principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
    tenant = TenantContext(id="tenant123", rate_limit_rps=10)
    event_name = "audit.test_event"
    data = {"test": "data"}
    
    # This should not raise an exception
    asyncio.run(audit(event_name, principal, tenant, data))
    print("✓ No EventStore audit test passed")


def test_audit_events_constants():
    """Test audit event constants."""
    print("Testing audit event constants...")
    
    assert AuditEvents.PLAN_REQUESTED == "audit.plan_requested"
    assert AuditEvents.PLAN_STARTED == "audit.plan_started"
    assert AuditEvents.PLAN_FAILED == "audit.plan_failed"
    assert AuditEvents.PLAN_COMPLETED == "audit.plan_completed"
    
    print("✓ Audit events constants test passed")


def test_audit_with_complex_data():
    """Test audit with complex data."""
    print("Testing audit with complex data...")
    
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
    
    # This should not raise an exception
    asyncio.run(audit(event_name, principal, tenant, data))
    print("✓ Complex data audit test passed")


def test_audit_with_event_store_failure():
    """Test that audit continues to work even if EventStore fails."""
    print("Testing audit with EventStore failure...")
    
    mock_event_store = Mock()
    mock_event_store._get_tenant_scoped_stream = Mock(side_effect=Exception("EventStore error"))
    mock_event_store.append = AsyncMock()
    
    configure_event_store(mock_event_store)
    
    principal = Principal(sub="user123", tenant_id="tenant123", scopes=[])
    tenant = TenantContext(id="tenant123", rate_limit_rps=10)
    event_name = "audit.test_event"
    data = {"test": "data"}
    
    # This should not raise an exception even if EventStore fails
    asyncio.run(audit(event_name, principal, tenant, data))
    print("✓ EventStore failure audit test passed")


def main():
    """Run all tests."""
    print("Running audit logger tests...\n")
    
    try:
        test_audit_basic()
        test_audit_with_event_store()
        test_audit_without_event_store()
        test_audit_events_constants()
        test_audit_with_complex_data()
        test_audit_with_event_store_failure()
        
        print("\n🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

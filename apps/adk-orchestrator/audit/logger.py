import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from security.models import Principal, TenantContext

# Configure audit logger
audit_logger = logging.getLogger("kyros.audit")
audit_logger.setLevel(logging.INFO)

# Only add handler if none exist (to avoid duplicate logs in tests)
if not audit_logger.handlers:
    # Create a handler that outputs structured JSON
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)
    audit_logger.propagate = False  # Prevent duplicate logs

# Optional EventStore dependency
_event_store = None

def configure_event_store(event_store):
    """Configure the EventStore for audit events. Optional."""
    global _event_store
    _event_store = event_store

async def audit(
    event_name: str, 
    principal: Principal, 
    tenant: TenantContext, 
    data: Dict[str, Any]
) -> None:
    """
    Log an audit event with structured JSON format and optionally append to EventStore.
    
    Args:
        event_name: Name of the audit event (e.g., "audit.plan_requested")
        principal: The authenticated principal performing the action
        tenant: The tenant context
        data: Additional event data
    """
    # Create structured audit log entry
    audit_entry = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event_name,
        "actor": principal.sub,
        "tenant_id": tenant.id,
        "data": data
    }
    
    # Log the structured JSON
    audit_logger.info(json.dumps(audit_entry))
    
    # Optionally append to EventStore if configured
    if _event_store is not None:
        try:
            # Create tenant-scoped stream name
            stream_name = _event_store._get_tenant_scoped_stream("audit", tenant.id)
            
            # Create event for EventStore
            event = {
                "event_type": event_name,
                "timestamp": audit_entry["ts"],
                "actor": principal.sub,
                "tenant_id": tenant.id,
                "data": data
            }
            
            await _event_store.append(stream_name, [event])
        except Exception as e:
            # Log error but don't fail the audit call
            audit_logger.error(f"Failed to append audit event to EventStore: {e}")

# Predefined audit event names
class AuditEvents:
    PLAN_REQUESTED = "audit.plan_requested"
    PLAN_STARTED = "audit.plan_started"
    PLAN_FAILED = "audit.plan_failed"
    PLAN_COMPLETED = "audit.plan_completed"

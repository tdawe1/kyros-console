import pytest
import tempfile
import os
from security.models import TenantContext
from billing.budget import enforce_budget, BudgetExceededError

def test_budget_noop_when_no_database():
    """Test that budget enforcement is a no-op when no database exists."""
    tenant = TenantContext(
        id="test-tenant",
        rate_limit_rps=5,
        model_caps={}
    )
    
    # Should not raise any exception
    enforce_budget(tenant, estimated_cents=100)

def test_budget_noop_when_database_exists_but_empty():
    """Test that budget enforcement is a no-op when database exists but is empty."""
    tenant = TenantContext(
        id="test-tenant",
        rate_limit_rps=5,
        model_caps={}
    )
    
    # Create a temporary empty database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name
    
    try:
        # Temporarily replace the budget database path
        original_dir = os.path.dirname(__file__)
        budget_dir = os.path.join(original_dir, "billing")
        os.makedirs(budget_dir, exist_ok=True)
        
        # Create empty database file
        empty_db_path = os.path.join(budget_dir, "budgets.db")
        with open(empty_db_path, "w") as f:
            f.write("")
        
        # Should not raise any exception (no-op implementation)
        enforce_budget(tenant, estimated_cents=100)
        
        # Clean up
        os.remove(empty_db_path)
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(empty_db_path):
            os.remove(empty_db_path)
        raise e

if __name__ == "__main__":
    test_budget_noop_when_no_database()
    test_budget_noop_when_database_exists_but_empty()
    print("All budget tests passed!")

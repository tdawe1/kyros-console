#!/usr/bin/env python3
"""
Test script to verify rate limiting functionality.
This script sends multiple requests to test the rate limiting.
"""
import requests
import time
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "your-test-jwt-token-here"  # Replace with actual test token

def create_test_request() -> Dict[str, Any]:
    """Create a test run request payload."""
    return {
        "pr": {
            "repo": "test/repo",
            "pr_number": 123,
            "branch": "feature/test",
            "head_sha": "abc123def456"
        },
        "mode": "plan",
        "labels": ["test"],
        "extra": {}
    }

def send_request(session: requests.Session, headers: Dict[str, str]) -> requests.Response:
    """Send a single request to the plan endpoint."""
    payload = create_test_request()
    return session.post(
        f"{BASE_URL}/v1/runs/plan",
        json=payload,
        headers=headers
    )

def test_rate_limiting():
    """Test rate limiting by sending requests faster than the limit."""
    print("Testing rate limiting...")
    print("Sending 10 requests at 1 request per second (should be under 5/second limit)")
    
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    session = requests.Session()
    
    # Test 1: Send requests at 1 req/sec (should all succeed)
    print("\n=== Test 1: 1 request/second (should all succeed) ===")
    for i in range(5):
        response = send_request(session, headers)
        print(f"Request {i+1}: Status {response.status_code}")
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            print(f"  Rate limited! Retry-After: {retry_after}")
        time.sleep(1)
    
    # Test 2: Send requests rapidly (should hit rate limit)
    print("\n=== Test 2: Rapid requests (should hit rate limit) ===")
    rate_limited_count = 0
    for i in range(10):
        response = send_request(session, headers)
        print(f"Request {i+1}: Status {response.status_code}")
        if response.status_code == 429:
            rate_limited_count += 1
            retry_after = response.headers.get('Retry-After')
            print(f"  Rate limited! Retry-After: {retry_after}")
        time.sleep(0.1)  # 10 requests per second
    
    print(f"\nSummary: {rate_limited_count}/10 requests were rate limited")
    
    if rate_limited_count > 0:
        print("✅ Rate limiting is working!")
    else:
        print("❌ Rate limiting may not be working properly")

if __name__ == "__main__":
    print("Rate Limiting Test Script")
    print("=" * 50)
    print(f"Target URL: {BASE_URL}/v1/runs/plan")
    print("Note: Make sure the server is running and you have a valid JWT token")
    print()
    
    # Uncomment the line below to run the test
    # test_rate_limiting()
    
    print("To run this test:")
    print("1. Start the orchestrator server")
    print("2. Update TEST_TOKEN with a valid JWT token")
    print("3. Uncomment the test_rate_limiting() call")
    print("4. Run: python test_rate_limits.py")

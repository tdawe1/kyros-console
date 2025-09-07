#!/usr/bin/env python3
"""
Test script to verify JWT authentication implementation.
"""

import requests
import json
import sys
import os

# Add the apps/adk-orchestrator directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'adk-orchestrator'))

from security.jwt import create_dev_token

def test_server():
    base_url = "http://localhost:8000"
    
    print("Testing JWT Authentication Implementation")
    print("=" * 50)
    
    # Test 1: Health check (no auth required)
    print("\n1. Testing health endpoint (no auth)...")
    try:
        response = requests.get(f"{base_url}/healthz", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    # Test 2: Create a valid JWT token
    print("\n2. Creating valid JWT token...")
    token = create_dev_token("user123", "tenant456", ["read", "write"])
    print(f"   Token: {token[:50]}...")
    
    # Test 3: Test /v1/runs/plan with valid token
    print("\n3. Testing /v1/runs/plan with valid token...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "pr": {
            "repo": "test/repo",
            "pr_number": 123,
            "branch": "feature/test",
            "head_sha": "abc123"
        },
        "mode": "plan",
        "labels": ["test"],
        "extra": {}
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/runs/plan",
            headers=headers,
            json=payload,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Test with invalid token
    print("\n4. Testing /v1/runs/plan with invalid token...")
    headers = {"Authorization": "Bearer invalid_token"}
    try:
        response = requests.post(
            f"{base_url}/v1/runs/plan",
            headers=headers,
            json=payload,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Test without token
    print("\n5. Testing /v1/runs/plan without token...")
    try:
        response = requests.post(
            f"{base_url}/v1/runs/plan",
            json=payload,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Test CORS
    print("\n6. Testing CORS with localhost:3001...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "http://localhost:3001"
    }
    try:
        response = requests.post(
            f"{base_url}/v1/runs/plan",
            headers=headers,
            json=payload,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers: {dict(response.headers).get('Access-Control-Allow-Origin', 'Not set')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_server()

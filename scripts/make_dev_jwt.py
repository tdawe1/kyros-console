#!/usr/bin/env python3
"""
Development helper to create JWT tokens for testing.

Usage:
    python scripts/make_dev_jwt.py --sub user123 --tenant tenant456
    python scripts/make_dev_jwt.py --sub user123 --tenant tenant456 --scopes read write
    python scripts/make_dev_jwt.py --sub user123 --tenant tenant456 --expires 24
"""

import argparse
import sys
import os

# Add the apps/adk-orchestrator directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'adk-orchestrator'))

# Use the virtual environment's Python
venv_python = os.path.join(os.path.dirname(__file__), '..', 'apps', 'adk-orchestrator', 'venv', 'bin', 'python')
if os.path.exists(venv_python):
    sys.executable = venv_python

from security.jwt import create_dev_token


def main():
    parser = argparse.ArgumentParser(description='Create a development JWT token')
    parser.add_argument('--sub', required=True, help='Subject (user ID)')
    parser.add_argument('--tenant', required=True, help='Tenant ID')
    parser.add_argument('--scopes', nargs='*', default=[], help='Authorization scopes')
    parser.add_argument('--expires', type=int, default=1, help='Expiration time in hours (default: 1)')
    
    args = parser.parse_args()
    
    token = create_dev_token(
        sub=args.sub,
        tenant_id=args.tenant,
        scopes=args.scopes,
        expires_in_hours=args.expires
    )
    
    print(f"JWT Token (expires in {args.expires} hour(s)):")
    print(token)
    print()
    print("Use with curl:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/v1/runs/plan')


if __name__ == '__main__':
    main()

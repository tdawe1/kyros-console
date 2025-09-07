#!/bin/bash
cd /home/thomas/kyros-console/kyros-console/apps/adk-orchestrator
export JWT_SECRET=devsecret
./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000

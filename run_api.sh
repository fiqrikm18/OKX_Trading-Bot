#!/bin/bash
echo "🚀 Starting SaaS API Server..."
uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

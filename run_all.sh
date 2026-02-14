#!/bin/bash

# Load environment variables if needed, or rely on .env handled by apps
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "🚀 Starting OKX Trading Bot & Dashboard..."

# Trap SIGINT to kill background processes
trap "kill 0" SIGINT

# Start Frontend (React + Vite) in background
echo "📊 Starting Frontend..."
cd frontend
npm run dev &
cd ..

# Start Bot via API Server (hosting Bot)
echo "🤖 Starting API Server..."
AUTO_START_BOT=true uv run uvicorn src.api:app --host 0.0.0.0 --port 8000 &

# Wait for both
wait

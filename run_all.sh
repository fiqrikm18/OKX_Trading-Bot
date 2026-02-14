#!/bin/bash

# Load environment variables if needed, or rely on .env handled by apps
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "🚀 Starting OKX Trading Bot & Dashboard..."

# Trap SIGINT to kill background processes
trap "kill 0" SIGINT

# Start Dashboard in background
echo "📊 Starting Dashboard..."
uv run streamlit run dashboard.py &

# Start Bot in background
echo "🤖 Starting Trading Bot..."
uv run python main.py &

# Wait for both
wait

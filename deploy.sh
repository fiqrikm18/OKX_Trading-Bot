#!/bin/bash

echo "🚀 STARTING ULTRA-FAST DEPLOYMENT (UV + BUN)..."

# 1. Update System & Install Basic Tools
echo "📦 Updating Linux..."
sudo apt update -y
sudo apt install curl unzip -y

# 2. Install uv (Fast Python Installer)
echo "⚡ Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env # Load uv into current session

# 3. Install Bun (Fast JS Runtime for PM2)
echo "🍞 Installing Bun..."
curl -fsSL https://bun.sh/install | bash
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# 4. Set up Python Environment with uv
echo "🐍 Setting up venv with uv..."
# Install dependencies from uv.lock (super fast & determinstic)
uv sync

# Activate venv is not strictly needed if we point to the python binary, 
# but uv sync creates .venv by default.

# 5. Install PM2 using Bun
echo "⚙️ Installing PM2 via Bun..."
bun add -g pm2

# 6. Start the Bot & Dashboard
echo "🤖 Starting AI Trader & Dashboard..."

# Stop existing if running
# Start Bot (API Server)
AUTO_START_BOT=true pm2 start "uv run uvicorn src.api:app --host 0.0.0.0 --port 8000" --name "ai-trader"

# Build & Serve Frontend
echo "🏗️ Building Frontend..."
cd frontend
npm install
npm run build
pm2 serve dist 5173 --name "okx-frontend" --spa
cd ..

# 7. Save State
echo "💾 Saving PM2 State..."
pm2 save

echo "-----------------------------------------------"
echo "✅ DEPLOYMENT COMPLETE!"
echo "-----------------------------------------------"
echo "👉 Check logs:   pm2 logs"
echo "👉 Dashboard:    http://<your-ip>:5173"
echo "-----------------------------------------------"

# Startup command (PM2 might ask you to run a command after this)
pm2 startup

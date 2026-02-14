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
pm2 delete ai-trader 2>/dev/null
pm2 delete ai-dashboard 2>/dev/null

# Start Bot
pm2 start main.py --name "ai-trader" --interpreter ./.venv/bin/python3

# Start Dashboard (Streamlit needs specific command structure with PM2)
pm2 start "uv run streamlit run dashboard.py --server.port 8501 --server.headingsWithAnchors false" --name "ai-dashboard"

# 7. Save State
echo "💾 Saving PM2 State..."
pm2 save

echo "-----------------------------------------------"
echo "✅ DEPLOYMENT COMPLETE!"
echo "-----------------------------------------------"
echo "👉 Check logs:   pm2 logs"
echo "👉 Dashboard:    http://<your-ip>:8501"
echo "-----------------------------------------------"

# Startup command (PM2 might ask you to run a command after this)
pm2 startup

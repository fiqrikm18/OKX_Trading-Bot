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
# remove old venv if exists to avoid conflicts
rm -rf .venv
uv venv

# Activate venv
source .venv/bin/activate

# Install libraries using uv (Parallel & Cached - Super Fast)
echo "📚 Installing Python Libraries..."
uv pip install ccxt pandas pandas_ta scikit-learn numpy requests python-dotenv

# 5. Install PM2 using Bun
echo "⚙️ Installing PM2 via Bun..."
bun add -g pm2

# 6. Start the Bot
echo "🤖 Starting AI Trader..."

# Stop existing if running
pm2 delete ai-trader 2>/dev/null

# Start using the Python executable inside the .venv folder
pm2 start main.py --name "ai-trader" --interpreter ./.venv/bin/python3

# 7. Save State
echo "💾 Saving PM2 State..."
pm2 save

echo "-----------------------------------------------"
echo "✅ DEPLOYMENT COMPLETE!"
echo "-----------------------------------------------"
echo "👉 Check logs:   pm2 logs ai-trader"
echo "👉 Stop bot:     pm2 stop ai-trader"
echo "👉 Monitor:      pm2 monit"
echo "-----------------------------------------------"

# Startup command (PM2 might ask you to run a command after this)
pm2 startup

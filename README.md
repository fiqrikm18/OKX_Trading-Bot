# OKX AI Trading Bot 🤖

A fully autonomous, AI-powered trading bot for the OKX exchange. This bot leverages Machine Learning (Random Forest) and Technical Analysis to identify trading opportunities, manage risk dynamically, and execute trades with precision.

Designed for both **Paper Trading** (simulation) and **Live Trading** (real capital), featuring real-time Discord notifications and robust state management.

---

## 🚀 Key Features

* **🧠 AI-Powered Signals**: Uses a Random Forest Classifier trained on real-time market data (RSI, SMA, Returns, Volume) to predict price direction.
* **📊 Dynamic Symbol Selection**: Automatically scans and selects the most volatile and high-volume pairs (USDT swaps) to trade.
* **🛡️ Advanced Risk Management**:
  * **Dynamic Position Sizing**: Calculates position size based on account balance and risk percentage.
  * **Trailing Stop Loss**: Secures profits as the price moves in your favor.
  * **Take Profit & Stop Loss**: Automated exit strategies based on predefined targets.
* **🔔 Discord Integration**: Real-time notifications for trade entries, exits, and PnL updates sent directly to your Discord server.
* **🔄 State Persistence**: Saves trade state to `trade_state.json` to resume operations seamlessly after restarts.
* **⚡ High-Performance Deployment**: Optimized for speed using `uv` (fast Python package installer) and `Bun` (fast JS runtime for PM2).

---

## 🛠️ Prerequisites

* **Python 3.12+**
* **Python 3.12+**
* **OKX Account**: API Key, Secret, and Passphrase (with **Trade** permissions enabled).
* **Discord Webhook** (Optional): For receiving trade alerts.

---

## 📦 Installation

This project is optimized for deployment on Linux/macOS using `uv` for ultra-fast dependency management and `Vite` for the frontend.

### Option 1: Quick Deployment (Recommended)

Use the included deployment script to set up everything automatically (installs `uv`, `bun`, `pm2`, Backend dependencies, and builds Foreground).

```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Development

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/OKXTradingBot.git
    cd OKXTradingBot
    ```

2. **Backend Setup (using `uv`):**

    ```bash
    # Install uv if not installed
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Sync python dependencies
    uv sync
    ```

3. **Frontend Setup (React + Vite):**

    ```bash
    cd frontend
    npm install
    cd ..
    ```

---

## ⚙️ Configuration

1. **Environment Variables**:
    Copy the example environment file and configure your keys.

    ```bash
    cp .env.example .env
    ```

    Edit `.env` and fill in your details:

    ```ini
    OKX_API_KEY=your_api_key
    OKX_SECRET_KEY=your_secret_key
    OKX_PASSWORD=your_passphrase
    DISCORD_WEBHOOK_URL=your_discord_webhook_url

    # Database (Postgres)
    DB_HOST=127.0.0.1
    DB_USER=postgres
    DB_PASS=postgres
    DB_NAME=okx_trading

    # API Security
    JWT_SECRET_KEY=your_secure_secret
    ACCESS_TOKEN_EXPIRE_MINUTES=1440
    ```

---

## 🏃 Usage

### Run Locally (Dev Mode)

To start both the **FastAPI Backend** and **React Frontend** in local development mode:

```bash
chmod +x run_all.sh
./run_all.sh
```

* **Dashboard**: `http://localhost:5173`
* **API Specs**: `http://localhost:8000/docs`

### Run in Background (PM2 Production)

If you used `deploy.sh`, services are managed by PM2.

* **View Logs**: `pm2 logs`
* **Monitor Status**: `pm2 monit`
* **Stop All**: `pm2 stop all`
* **Restart All**: `pm2 restart all`
* **Dashboard URL**: `http://<your-server-ip>:5173`

---

## 📂 Project Structure

* `src/`: Backend Source code (DDD Structure).
  * `config/`: Settings & Environment.
  * `domain/`: Business logic (AI, Market Analysis).
  * `infrastructure/`: External adapters (Exchange, Discord, Postgres).
  * `application/`: Application services.
  * `interfaces/api/`: FastAPI Routes & Auth.
* `frontend/`: React + Vite Frontend.
  * `src/pages/`: Dashboard & Login screens.
  * `src/components/`: Reusable UI components.
* `deploy.sh`: Automated production deployment.
* `run_all.sh`: Local development launcher.
* `pyproject.toml`: Python dependencies.

---

## ⚠️ Disclaimer

**Trading cryptocurrencies involves significant risk.**

1. **Create Admin User**:
    To access the dashboard, create an initial admin account:

    ```bash
    uv run python create_user.py
    ```

## 🗺️ Roadmap Status

* [x] **Core Trading Engine** (AI Signals, Risk Mgmt)
* [x] **Database** (PostgreSQL Persistence)
* [x] **API Layer** (FastAPI, JWT Auth)
* [x] **Frontend** (React, Tailwind, Recharts)
  * [x] Real-time PnL Updates
  * [x] Trade History & Filtering
  * [x] Responsive Mobile Layout
  * [x] Manual Bot Control (Start/Stop)

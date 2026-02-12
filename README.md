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
* **OKX Account**: API Key, Secret, and Passphrase (with **Trade** permissions enabled).
* **Discord Webhook** (Optional): For receiving trade alerts.

---

## 📦 Installation

This project is optimized for deployment on Linux/macOS using `uv` for ultra-fast dependency management.

### Option 1: Quick Deployment (Recommended)

Use the included deployment script to set up everything automatically (installs `uv`, `bun`, `pm2`, and dependencies).

```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/OKXTradingBot.git
    cd OKXTradingBot
    ```

2. **Set up a virtual environment (using `uv` or `venv`):**

    ```bash
    # Using uv (Recommended)
    uv venv
    source .venv/bin/activate
    uv pip install -r pyproject.toml
    
    # OR using standard pip
    python3 -m venv .venv
    source .venv/bin/activate
    pip install ccxt pandas pandas_ta scikit-learn numpy requests python-dotenv
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
    ```

2. **Bot Settings (`main.py`)**:
    You can adjust trading parameters directly in the `0. CONFIGURATION` section of `main.py`:

    * `TIMEFRAME`: Candle timeframe (default: `"15m"`).
    * `LEVERAGE`: Trading leverage (default: `10`).
    * `RISK_PER_TRADE_PCT`: Risk per trade as a decimal (default: `0.10` for 10%).
    * `REAL_TRADING`: Set to `True` to trade with real money. **Default is `False` (Paper Trading).**

---

## 🏃 Usage

### Run Locally

To start the bot in your terminal:

```bash
python main.py
```

### Run in Background (PM2)

If you used `deploy.sh`, the bot is already running under PM2.

* **View Logs**: `pm2 logs ai-trader`
* **Monitor Status**: `pm2 monit`
* **Stop Bot**: `pm2 stop ai-trader`
* **Restart Bot**: `pm2 restart ai-trader`

---

## 📂 Project Structure

* `main.py`: Core logic for the trading bot (AI, execution, risk management).
* `deploy.sh`: Automated deployment script.
* `trade_state.json`: Stores active trades and PnL history (auto-generated).
* `pyproject.toml`: Python dependencies and project metadata.
* `.env`: Configuration file for API keys (not committed).

---

## ⚠️ Disclaimer

**Trading cryptocurrencies involves significant risk and can result in the loss of your capital.**

This software is for educational purposes only. The authors and contributors are not responsible for any financial losses or damages incurred while using this bot. Use it at your own risk. **Always test thoroughly in Paper Trading mode before using real funds.**

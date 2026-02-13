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

# Roadmap

## 📅 Feature Checklist

* [ ] **1.A Market Regime Filter** (Trend Alignment)
* [ ] **1.B Smart Volatility Stops** (ATR-based dynamic stops)
* [ ] **1.C Sentiment Analysis** (Funding Rates)
* [ ] **2.A Daily Circuit Breaker** (Max daily loss limit)
* [ ] **2.B Breakeven Trigger** (Secure profits early)
* [ ] **3.A Telegram Bot Control** (Remote management)
* [ ] **3.B Web Dashboard** (Streamlit visualization)
* [ ] **3.C Database Integration** (SQLite migration)
* [ ] **4.A Limit Orders** (Maker fee savings)
* [ ] **4.B DCA Strategy** (Average down logic)

## 1. 🧠 AI & Strategy Enhancements (The Brain)

### A. Market Regime Filter ("Don't Swim Against the Tide")

**The Problem:** Your bot might try to LONG an altcoin while Bitcoin is crashing 10%. This usually fails.
**The Feature:** Before opening any trade, check Bitcoin's trend.

* If BTC price < BTC 200 EMA -> Bear Market (Only allow SHORTs).
* If BTC price > BTC 200 EMA -> Bull Market (Only allow LONGs).
**Why:** Increases win rate significantly by aligning with the global market direction.

### B. Smart Volatility Stops (ATR)

**The Problem:** Your current TRAILING_STOP_PCT = 0.02 (2%) is static.

* For a stable coin (like BTC), 2% is too wide.
* For a meme coin (like PEPE), 2% is too tight and you will get "stopped out" by normal noise.
**The Feature:** Use ATR (Average True Range) to calculate stops.
* Stop Loss = Current Price - (ATR * 2)
**Why:** It adapts to the coin's volatility dynamically.

### C. Sentiment Analysis (Funding Rates)

**The Problem:** Technical indicators (RSI/SMA) lag behind price.
**The Feature:** Use Funding Rates as a sentiment feature for your AI.

* High Positive Funding = Market is greedy (Potential Short signal).
* High Negative Funding = Market is fearful (Potential Long signal).
**How:** `exchange.fetch_funding_rate(symbol)` and add it to your DataFrame.

## 2. 🛡️ Risk Management (The Shield)

### A. Daily Circuit Breaker

**The Problem:** Sometimes the market goes crazy (flash crash) and the AI starts making bad decisions repeatedly.
**The Feature:** A "Max Daily Loss" limit.

* Example: If Daily Loss > 10%, Stop Trading for 24 hours.
**Why:** Prevents one bad day from wiping out your account.

### B. Breakeven Trigger

**The Problem:** You are up 4% (Target is 5%), but then price drops and hits your Stop Loss (-2%). You turned a win into a loss.
**The Feature:** Move Stop Loss to Entry Price once profit hits X% (e.g., 2.5%).
**Why:** Ensures a "Risk-Free Trade" once the price moves in your favor.

## 3. 🎮 Usability & Control (The Body)

### A. Telegram Bot Control (Interactive)

**The Problem:** Currently, you can only watch Discord logs. You can't control the bot without SSH-ing into the server.
**The Feature:** Use a Telegram Bot API to send commands to your bot via chat.

* `/status` -> Bot replies with current PnL and open positions.
* `/sell BTC` -> Forces the bot to close the BTC position immediately.
* `/stop` -> Pauses the bot.
**Why:** Gives you control from your phone anywhere in the world.

### B. Web Dashboard (Streamlit)

**The Feature:** Build a simple dashboard using Python Streamlit that reads your `trade_state.json`.
**Why:** Visualize your profit curve, win rate, and trade history in a nice graph instead of text logs.

### C. Database Integration (SQLite)

**The Problem:** `trade_state.json` is risky. If the file gets corrupted, you lose data. It also doesn't store history (closed trades).
**The Feature:** Move from JSON to SQLite (a single-file database).

* **Table 1:** `active_trades` (Current positions).
* **Table 2:** `trade_history` (Past performance for analysis).

## 4. ⚡ Execution (The Hands)

### A. Limit Orders (Maker Fees)

**The Problem:** You currently use "Market Orders" (Taker). These have higher fees (usually 0.05%).
**The Feature:** Place "Limit Orders" (Maker) slightly below price and wait for a fill.
**Why:** Maker fees are often much lower (sometimes 0.02% or even 0%), saving you money on every trade.

### B. DCA (Dollar Cost Averaging) / Grid

**The Feature:** Instead of closing at a loss, buy more if the price drops -2%, -4%, -6% to lower your average entry price.
**Warning:** This is risky (Martingale strategy), but very popular for "recovering" losing trades in ranging markets.

---

🌟 **Priority Features (Implemented First):**
Since we are running on a small account ($5) where one bad trade hurts, we are prioritizing implementing:

1. **2.B (Breakeven Trigger)**
2. **1.B (ATR Stops)**
to protect capital.

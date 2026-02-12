import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import json
import os
import time
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from dotenv import load_dotenv

# ==========================================
# 0. CONFIGURATION
# ==========================================
load_dotenv()

API_KEY = os.getenv("OKX_API_KEY")
SECRET_KEY = os.getenv("OKX_SECRET_KEY")
PASSWORD = os.getenv("OKX_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not all([API_KEY, SECRET_KEY, PASSWORD]):
    print("❌ ERROR: Missing keys in .env")
    exit()

# --- $5 ACCOUNT SETTINGS ---
TIMEFRAME = "15m"
LEVERAGE = 10
MAX_POSITIONS = 1

# --- DYNAMIC RISK ---
RISK_PER_TRADE_PCT = 0.10  # 10% Risk
MIN_TRADE_SIZE = 2.0

# --- TARGETS ---
TRAILING_STOP_PCT = 0.02
ROE_TARGET = 0.3
TAKE_PROFIT_PCT = ROE_TARGET / LEVERAGE
CONFIDENCE_THRESHOLD = 0.65

REAL_TRADING = False  # CHANGE TO True FOR REAL MONEY
INITIAL_PAPER_BALANCE = 5.0

STATE_FILE = "trade_state.json"

exchange = ccxt.okx(
    {
        "apiKey": API_KEY,
        "secret": SECRET_KEY,
        "password": PASSWORD,
        "enableRateLimit": True,
        "options": {"defaultType": "swap"},
    }
)


# ==========================================
# 1. STATE MANAGER
# ==========================================
class TradeManager:
    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                    if "paper_balance" not in data:
                        data["paper_balance"] = INITIAL_PAPER_BALANCE
                    if "trades" not in data:
                        data["trades"] = {}
                    if "total_pnl" not in data:
                        data["total_pnl"] = 0.0
                    return data
            except:
                pass
        return {"trades": {}, "total_pnl": 0.0, "paper_balance": INITIAL_PAPER_BALANCE}

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f)

    def add_trade(self, symbol, data):
        self.state["trades"][symbol] = data
        self.save_state()

    def remove_trade(self, symbol, pnl):
        if symbol in self.state["trades"]:
            del self.state["trades"][symbol]
            self.state["total_pnl"] += pnl
            self.state["paper_balance"] += pnl
            self.save_state()

    def update_trailing(self, symbol, current_price):
        if symbol not in self.state["trades"]:
            return
        trade = self.state["trades"][symbol]
        if "best_price" not in trade:
            trade["best_price"] = trade["entry"]

        side = trade["side"]
        best = trade["best_price"]
        updated = False

        if side == "LONG" and current_price > best:
            trade["best_price"] = current_price
            updated = True
        elif side == "SHORT" and current_price < best:
            trade["best_price"] = current_price
            updated = True

        if updated:
            self.state["trades"][symbol] = trade
            self.save_state()

    def check_exit_conditions(self, symbol, current_price):
        if symbol not in self.state["trades"]:
            return None, 0.0
        trade = self.state["trades"][symbol]
        side = trade["side"]
        entry = trade["entry"]
        best = trade.get("best_price", entry)

        if side == "LONG":
            stop_price = best * (1 - TRAILING_STOP_PCT)
            if current_price < stop_price:
                return "STOP_LOSS", stop_price
            tp_price = entry * (1 + TAKE_PROFIT_PCT)
            if current_price >= tp_price:
                return "TAKE_PROFIT", tp_price
        elif side == "SHORT":
            stop_price = best * (1 + TRAILING_STOP_PCT)
            if current_price > stop_price:
                return "STOP_LOSS", stop_price
            tp_price = entry * (1 - TAKE_PROFIT_PCT)
            if current_price <= tp_price:
                return "TAKE_PROFIT", tp_price

        return None, 0.0


manager = TradeManager()


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def log_to_discord(message, level="info"):
    if not DISCORD_WEBHOOK_URL:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = 3447003 if level == "info" else 15158332
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            json={
                "embeds": [
                    {"description": f"**[{timestamp}]** {message}", "color": color}
                ]
            },
        )
    except:
        pass


def get_current_balance():
    if REAL_TRADING:
        try:
            balance = exchange.fetch_balance()
            return float(balance["USDT"]["free"])
        except:
            return 0.0
    else:
        return manager.state["paper_balance"]


def fetch_data(symbol, limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=limit)
        df = pd.DataFrame(
            bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        return df
    except:
        return None


def get_dynamic_symbols(limit=10):
    try:
        tickers = exchange.fetch_tickers()
        valid_pairs = []
        for symbol, data in tickers.items():
            raw = data.get("info", {})
            if raw.get("instType") == "SWAP" and "USDT" in raw.get("instId", ""):
                quote_vol = float(raw.get("volCcy24h", 0))
                if quote_vol > 1_000_000:
                    valid_pairs.append(
                        {
                            "symbol": symbol,
                            "change": (
                                abs(data["percentage"]) if data["percentage"] else 0
                            ),
                        }
                    )
        if not valid_pairs:
            return ["BTC/USDT:USDT", "ETH/USDT:USDT"]
        sorted_pairs = sorted(valid_pairs, key=lambda x: x["change"], reverse=True)
        return [item["symbol"] for item in sorted_pairs[:limit]]
    except:
        return ["BTC/USDT:USDT"]


# ==========================================
# 3. AI & EXECUTION
# ==========================================
def get_ai_signal(df):
    df["RSI"] = ta.rsi(df["close"], length=14)
    df["SMA"] = ta.sma(df["close"], length=20)
    df["Returns"] = df["close"].pct_change()
    df["Vol_Change"] = df["volume"].pct_change()
    df["Target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    df.dropna(inplace=True)
    if len(df) < 50:
        return "NEUTRAL", 0.0

    features = ["RSI", "SMA", "Returns", "Vol_Change"]
    model = RandomForestClassifier(
        n_estimators=100, min_samples_split=10, random_state=42
    )
    model.fit(df[features][:-1], df["Target"][:-1])
    latest = df[features].iloc[[-1]]
    prob_up = model.predict_proba(latest)[0][1]

    if prob_up > CONFIDENCE_THRESHOLD:
        return "LONG", prob_up
    elif prob_up < (1 - CONFIDENCE_THRESHOLD):
        return "SHORT", (1 - prob_up)
    return "NEUTRAL", 0.0


def set_leverage(symbol):
    try:
        exchange.set_margin_mode("isolated", symbol)
        exchange.set_leverage(LEVERAGE, symbol)
    except:
        pass


def open_position(symbol, side, available_balance):
    target_margin = available_balance * RISK_PER_TRADE_PCT
    if target_margin < MIN_TRADE_SIZE:
        if available_balance > MIN_TRADE_SIZE:
            target_margin = MIN_TRADE_SIZE
        else:
            target_margin = available_balance * 0.95
        if target_margin < 1.0:
            return

    ticker = exchange.fetch_ticker(symbol)
    price = ticker["last"]
    amount_coins = (target_margin * LEVERAGE) / price

    total_pnl = manager.state["total_pnl"]
    pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

    log_to_discord(
        f"🚀 **OPENING {side}**: {symbol}\n"
        f"💰 Margin: ${target_margin:.2f}\n"
        f"💳 Balance: ${available_balance:.2f}\n"
        f"📊 Total PnL: {pnl_str}"
    )

    if REAL_TRADING:
        set_leverage(symbol)
        try:
            if side == "LONG":
                exchange.create_market_buy_order(symbol, amount_coins)
            elif side == "SHORT":
                exchange.create_market_sell_order(symbol, amount_coins)
        except Exception as e:
            log_to_discord(f"❌ Failed: {e}", "error")
            return

    manager.add_trade(
        symbol,
        {
            "symbol": symbol,
            "side": side,
            "entry": price,
            "amount": amount_coins,
            "margin": target_margin,
            "best_price": price,
        },
    )


def close_position(symbol, reason):
    if symbol not in manager.state["trades"]:
        return
    trade = manager.state["trades"][symbol]
    ticker = exchange.fetch_ticker(symbol)
    exit_price = ticker["last"]

    if REAL_TRADING:
        try:
            if trade["side"] == "LONG":
                exchange.create_market_sell_order(symbol, trade["amount"])
            elif trade["side"] == "SHORT":
                exchange.create_market_buy_order(symbol, trade["amount"])
        except Exception as e:
            log_to_discord(f"❌ Close Failed: {e}", "error")

    if trade["side"] == "LONG":
        pnl = (exit_price - trade["entry"]) * trade["amount"]
    else:
        pnl = (trade["entry"] - exit_price) * trade["amount"]

    # Calculate ROI%
    margin = trade.get("margin", 0)
    if margin == 0:
        margin = (trade["amount"] * trade["entry"]) / LEVERAGE
    roi_pct = (pnl / margin) * 100 if margin > 0 else 0

    manager.remove_trade(symbol, pnl)

    new_total_pnl = manager.state["total_pnl"]
    new_balance = (
        manager.state["paper_balance"] if not REAL_TRADING else get_current_balance()
    )

    total_str = (
        f"+${new_total_pnl:.2f}"
        if new_total_pnl >= 0
        else f"-${abs(new_total_pnl):.2f}"
    )
    trade_pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
    roi_str = f"+{roi_pct:.2f}%" if roi_pct >= 0 else f"{roi_pct:.2f}%"

    log_to_discord(
        f"🛑 **CLOSING**: {symbol}\n"
        f"📜 Reason: {reason}\n"
        f"💵 Trade PnL: **{trade_pnl_str} ({roi_str})**\n"
        f"💳 New Balance: **${new_balance:.2f}**\n"
        f"💰 Total PnL: **{total_str}**"
    )


# ==========================================
# 5. MAIN LOOP
# ==========================================
def run_bot():
    print(f"🤖 **AI TRADER STARTED** ($5 Account Mode)")
    log_to_discord(f"🤖 **Bot Live**")

    while True:
        try:
            # PHASE 1: MANAGE
            active_symbols = list(manager.state["trades"].keys())
            total_realized_pnl = manager.state["total_pnl"]
            current_bal = get_current_balance()

            print(
                f"\n--- 💳 Balance: ${current_bal:.2f} | 💰 Profit: ${total_realized_pnl:.4f} ---"
            )

            for symbol in active_symbols:
                trade = manager.state["trades"][symbol]
                ticker = exchange.fetch_ticker(symbol)
                current_price = ticker["last"]
                manager.update_trailing(symbol, current_price)
                exit_reason, exit_price = manager.check_exit_conditions(
                    symbol, current_price
                )

                if trade["side"] == "LONG":
                    pnl = (current_price - trade["entry"]) * trade["amount"]
                else:
                    pnl = (trade["entry"] - current_price) * trade["amount"]

                # ROI Calc for Console
                margin = trade.get("margin", 0)
                if margin == 0:
                    margin = (trade["amount"] * trade["entry"]) / LEVERAGE
                roi = (pnl / margin) * 100 if margin > 0 else 0

                pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                roi_str = f"+{roi:.1f}%" if roi >= 0 else f"{roi:.1f}%"

                print(
                    f"Holding {symbol} ({trade['side']}) | PnL: {pnl_str} ({roi_str})"
                )

                if exit_reason:
                    close_position(symbol, f"{exit_reason} (${exit_price:.4f})")

            # PHASE 2: SCAN
            if len(manager.state["trades"]) < MAX_POSITIONS:

                print(f"🔍 Scanning... (Bal: ${current_bal:.2f})")

                if current_bal > 2.0:
                    dynamic_list = get_dynamic_symbols(limit=10)
                    for symbol in dynamic_list:
                        if symbol in manager.state["trades"]:
                            continue
                        print(f"Analyzing {symbol}...")
                        df = fetch_data(symbol)
                        if df is not None:
                            signal, conf = get_ai_signal(df)
                            if signal != "NEUTRAL":
                                print(f"✅ SIGNAL: {signal} ({conf:.2f})")
                                open_position(symbol, signal, current_bal)
                                break
                else:
                    print("💤 Balance too low (< $2).")

            time.sleep(10)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_bot()

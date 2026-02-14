import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 0. CONFIGURATION
# ==========================================

API_KEY = os.getenv("OKX_API_KEY")
SECRET_KEY = os.getenv("OKX_SECRET_KEY")
PASSWORD = os.getenv("OKX_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

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
ATR_MULTIPLIER = 2.0

# --- PHASE 2 SETTINGS ---
MAX_DAILY_LOSS_PCT = 0.10
BREAKEVEN_TRIGGER_PCT = 0.025  # 2.5%

REAL_TRADING = False  # CHANGE TO True FOR REAL MONEY
INITIAL_PAPER_BALANCE = 5.0

STATE_FILE = "trade_state.json"

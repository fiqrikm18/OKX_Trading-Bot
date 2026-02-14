from datetime import datetime
from src.config.settings import TRAILING_STOP_PCT, TAKE_PROFIT_PCT, ATR_MULTIPLIER, INITIAL_PAPER_BALANCE, REAL_TRADING, BREAKEVEN_TRIGGER_PCT, MAX_DAILY_LOSS_PCT, LEVERAGE
from src.infrastructure.exchange.client import exchange_client
from src.infrastructure.persistence.postgres_repo import PostgresRepository


class TradeManager:
    def __init__(self, exchange_client=None):
        self.repo = PostgresRepository()
        self.exchange_client = exchange_client
        self.state = self.load_state()

    def load_state(self):
        trades = self.repo.load_trades()
        paper_bal = self.repo.load_state_value(
            "paper_balance", INITIAL_PAPER_BALANCE)
        total_pnl = self.repo.load_state_value("total_pnl", 0.0)
        daily_start = self.repo.load_state_value(
            "daily_start_balance", paper_bal)
        last_reset = self.repo.load_state_value(
            "last_reset_date", str(datetime.utcnow().date()))

        return {
            "trades": trades,
            "paper_balance": paper_bal,
            "total_pnl": total_pnl,
            "daily_start_balance": daily_start,
            "last_reset_date": last_reset
        }

    def save_state(self):
        # We save individual components now, but we can sync back state variables
        self.repo.save_state_value(
            "paper_balance", self.state["paper_balance"])
        self.repo.save_state_value("total_pnl", self.state["total_pnl"])
        self.repo.save_state_value(
            "daily_start_balance", self.state["daily_start_balance"])
        self.repo.save_state_value(
            "last_reset_date", self.state["last_reset_date"])
        # Trades are saved individually on add/update

    def add_trade(self, symbol, data):
        self.state["trades"][symbol] = data
        self.repo.save_trade(data)
        self.save_state()

    def update_trade_entry(self, symbol, new_entry, new_amount, new_margin):
        if symbol not in self.state["trades"]:
            return
        trade = self.state["trades"][symbol]
        trade["entry"] = new_entry
        trade["amount"] = new_amount
        trade["margin"] = new_margin
        trade["breakeven_active"] = False
        trade["dca_count"] = trade.get("dca_count", 0) + 1

        self.state["trades"][symbol] = trade
        self.repo.save_trade(trade)
        self.save_state()

    def remove_trade(self, symbol, pnl):
        if symbol in self.state["trades"]:
            del self.state["trades"][symbol]
            self.state["total_pnl"] += pnl
            self.state["paper_balance"] += pnl
            self.repo.close_trade(symbol)
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
            self.repo.save_trade(trade)  # Update DB
            self.save_state()

    def check_exit_conditions(self, symbol, current_price):
        if symbol not in self.state["trades"]:
            return None, 0.0
        trade = self.state["trades"][symbol]
        side = trade["side"]
        entry = trade["entry"]
        best = trade.get("best_price", entry)
        atr = trade.get("atr", 0.0)
        breakeven = trade.get("breakeven_active", False)

        # Calculate PnL / ROI for Breakeven Check
        if side == "LONG":
            pnl = (current_price - entry) * trade["amount"]
        else:
            pnl = (entry - current_price) * trade["amount"]

        margin = trade.get("margin", 0)
        if margin == 0:
            margin = (trade["amount"] * entry) / LEVERAGE
        roi_pct = (pnl / margin) if margin > 0 else 0

        # Trigger Breakeven
        if not breakeven and roi_pct >= BREAKEVEN_TRIGGER_PCT:
            trade["breakeven_active"] = True
            breakeven = True
            self.state["trades"][symbol] = trade
            self.repo.save_trade(trade)  # Persist flag
            self.save_state()
            print(
                f"🛡️ Breakeven Triggered for {symbol} (ROI: {roi_pct*100:.2f}%)")

        if side == "LONG":
            stop_price = best * (1 - TRAILING_STOP_PCT)
            if atr > 0:
                stop_price = best - (atr * ATR_MULTIPLIER)

            # If Breakeven is active, Stop must be at least Entry
            if breakeven:
                stop_price = max(stop_price, entry)

            if current_price < stop_price:
                return "STOP_LOSS", stop_price
            tp_price = entry * (1 + TAKE_PROFIT_PCT)
            if current_price >= tp_price:
                return "TAKE_PROFIT", tp_price
        elif side == "SHORT":
            stop_price = best * (1 + TRAILING_STOP_PCT)
            if atr > 0:
                stop_price = best + (atr * ATR_MULTIPLIER)

            # If Breakeven is active, Stop must be at most Entry
            if breakeven:
                stop_price = min(stop_price, entry)

            if current_price > stop_price:
                return "STOP_LOSS", stop_price
            tp_price = entry * (1 - TAKE_PROFIT_PCT)
            if current_price <= tp_price:
                return "TAKE_PROFIT", tp_price

        return None, 0.0

    def reset_daily_stats_if_needed(self):
        current_date = str(datetime.utcnow().date())
        if self.state.get("last_reset_date") != current_date:
            print(
                f"🔄 New Day Detected: Resetting Daily Stats ({current_date})")
            if REAL_TRADING and self.exchange_client:
                current_bal = self.exchange_client.fetch_balance()
            else:
                current_bal = self.state["paper_balance"]

            self.state["daily_start_balance"] = current_bal
            self.state["last_reset_date"] = current_date
            self.save_state()

    def check_circuit_breaker(self):
        start_bal = self.state.get("daily_start_balance", 1.0)
        if REAL_TRADING and self.exchange_client:
            current_bal = self.exchange_client.fetch_balance()
        else:
            current_bal = self.state["paper_balance"]

        unrealized_pnl = 0.0
        if self.exchange_client:
            for symbol, trade in self.state["trades"].items():
                try:
                    ticker = self.exchange_client.fetch_ticker(symbol)
                    current_price = ticker["last"]
                    if trade["side"] == "LONG":
                        pnl = (current_price -
                               trade["entry"]) * trade["amount"]
                    else:
                        pnl = (trade["entry"] - current_price) * \
                            trade["amount"]
                    unrealized_pnl += pnl
                except:
                    pass

        current_equity = current_bal + unrealized_pnl
        pnl_pct = (current_equity - start_bal) / start_bal

        # Log Equity History
        self.repo.log_equity(current_bal, current_equity,
                             self.state["total_pnl"])

        return pnl_pct < -MAX_DAILY_LOSS_PCT, pnl_pct

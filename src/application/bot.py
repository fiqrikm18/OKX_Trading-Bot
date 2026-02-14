import time
from src.config.settings import RISK_PER_TRADE_PCT, MIN_TRADE_SIZE, LEVERAGE, REAL_TRADING, MAX_POSITIONS, MAX_DAILY_LOSS_PCT
from src.infrastructure.exchange.client import exchange_client
from src.infrastructure.persistence.state import TradeManager
from src.infrastructure.notification.discord import log_to_discord
from src.domain.analysis.market import fetch_data, get_dynamic_symbols, get_market_regime
from src.domain.analysis.ai_scanner import get_ai_signal


class TradingBot:
    def __init__(self):
        self.manager = TradeManager(exchange_client)

    def get_current_balance(self):
        if REAL_TRADING:
            return exchange_client.fetch_balance()
        else:
            return self.manager.state["paper_balance"]

    def set_leverage(self, symbol):
        exchange_client.set_leverage(symbol)

    def open_position(self, symbol, side, available_balance, atr_value):
        target_margin = available_balance * RISK_PER_TRADE_PCT
        if target_margin < MIN_TRADE_SIZE:
            if available_balance > MIN_TRADE_SIZE:
                target_margin = MIN_TRADE_SIZE
            else:
                target_margin = available_balance * 0.95
            if target_margin < 1.0:
                return

        ticker = exchange_client.fetch_ticker(symbol)
        price = ticker["last"]
        amount_coins = (target_margin * LEVERAGE) / price

        total_pnl = self.manager.state["total_pnl"]
        pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

        log_to_discord(
            f"🚀 **OPENING {side}**: {symbol}\n"
            f"💰 Margin: ${target_margin:.2f}\n"
            f"💳 Balance: ${available_balance:.2f}\n"
            f"📊 Total PnL: {pnl_str}"
        )

        if REAL_TRADING:
            self.set_leverage(symbol)
            try:
                if side == "LONG":
                    exchange_client.create_market_buy_order(
                        symbol, amount_coins)
                elif side == "SHORT":
                    exchange_client.create_market_sell_order(
                        symbol, amount_coins)
            except Exception as e:
                log_to_discord(f"❌ Failed: {e}", "error")
                return

        self.manager.add_trade(
            symbol,
            {
                "symbol": symbol,
                "side": side,
                "entry": price,
                "amount": amount_coins,
                "margin": target_margin,
                "best_price": price,
                "atr": atr_value,
                "breakeven_active": False,
            },
        )

    def close_position(self, symbol, reason):
        if symbol not in self.manager.state["trades"]:
            return
        trade = self.manager.state["trades"][symbol]
        ticker = exchange_client.fetch_ticker(symbol)
        exit_price = ticker["last"]

        if REAL_TRADING:
            try:
                if trade["side"] == "LONG":
                    exchange_client.create_market_sell_order(
                        symbol, trade["amount"])
                elif trade["side"] == "SHORT":
                    exchange_client.create_market_buy_order(
                        symbol, trade["amount"])
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

        self.manager.remove_trade(symbol, pnl)

        new_total_pnl = self.manager.state["total_pnl"]
        new_balance = (
            self.manager.state["paper_balance"] if not REAL_TRADING else self.get_current_balance(
            )
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

    def run(self):
        print(f"🤖 **AI TRADER STARTED** (DDD Refactored)")
        log_to_discord(f"🤖 **Bot Live**")

        while True:
            try:
                # PHASE 1: MANAGE
                active_symbols = list(self.manager.state["trades"].keys())
                total_realized_pnl = self.manager.state["total_pnl"]
                current_bal = self.get_current_balance()

                print(
                    f"\n--- 💳 Balance: ${current_bal:.2f} | 💰 Profit: ${total_realized_pnl:.4f} ---"
                )

                for symbol in active_symbols:
                    trade = self.manager.state["trades"][symbol]
                    ticker = exchange_client.fetch_ticker(symbol)
                    current_price = ticker["last"]
                    self.manager.update_trailing(symbol, current_price)
                    exit_reason, exit_price = self.manager.check_exit_conditions(
                        symbol, current_price
                    )

                    if trade["side"] == "LONG":
                        pnl = (current_price -
                               trade["entry"]) * trade["amount"]
                    else:
                        pnl = (trade["entry"] - current_price) * \
                            trade["amount"]

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
                        self.close_position(
                            symbol, f"{exit_reason} (${exit_price:.4f})")

                # PHASE 2: SCAN
                if len(self.manager.state["trades"]) < MAX_POSITIONS:

                    # Check Circuit Breaker
                    self.manager.reset_daily_stats_if_needed()
                    breaker_triggered, daily_pnl_pct = self.manager.check_circuit_breaker()

                    if breaker_triggered:
                        print(
                            f"🛑 CIRCUIT BREAKER TRIGGERED! Daily Loss: {daily_pnl_pct*100:.2f}% > {MAX_DAILY_LOSS_PCT*100}%")
                        print("Scanning Paused for today.")
                        time.sleep(60)  # Wait longer
                        continue

                    regime = get_market_regime()
                    print(
                        f"🔍 Scanning... Regime: {regime} (Balance: ${current_bal:.2f} | Daily: {daily_pnl_pct*100:.2f}%)")

                    if current_bal > 2.0:
                        dynamic_list = get_dynamic_symbols(limit=10)
                        for symbol in dynamic_list:
                            if symbol in self.manager.state["trades"]:
                                continue
                            print(f"Analyzing {symbol}...")
                            df = fetch_data(symbol)
                            if df is not None:
                                signal, conf, atr = get_ai_signal(df)

                                # Regime Filter
                                if regime == "BULL" and signal == "SHORT":
                                    print(
                                        f"⚠️ Signal SHORT ignored (Bull Market)")
                                    continue
                                if regime == "BEAR" and signal == "LONG":
                                    print(f"⚠️ Signal LONG ignored (Bear Market)")
                                    continue

                                if signal != "NEUTRAL":
                                    print(
                                        f"✅ SIGNAL: {signal} ({conf:.2f}) | ATR: {atr:.4f}")
                                    self.open_position(
                                        symbol, signal, current_bal, atr)
                                    break
                    else:
                        print("💤 Balance too low (< $2).")

                time.sleep(10)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)

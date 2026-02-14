import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from src.config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
import os


class TelegramService:
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.app = None
        self.loop = asyncio.new_event_loop()
        self.thread = None

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
            return

        # Access shared state in a thread-safe way (mostly ok for reading)
        bal = self.bot_instance.get_current_balance()
        pnl = self.bot_instance.manager.state["total_pnl"]
        trades = self.bot_instance.manager.state["trades"]

        msg = f"🤖 **Status Report**\n\n"
        msg += f"💳 Balance: ${bal:.2f}\n"
        msg += f"💰 Total PnL: ${pnl:.2f}\n"
        msg += f"📊 Active Positions: {len(trades)}\n"

        for symbol, trade in trades.items():
            entry = trade["entry"]
            side = trade["side"]
            pnl_val = 0.0  # Calculate estimated PnL if possible, or just show entry
            msg += f"- {symbol} ({side}) @ ${entry:.4f}\n"

        await update.message.reply_text(msg)

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
            return
        # We need a stop flag in the bot
        self.bot_instance.stop_requested = True
        await update.message.reply_text("🛑 Stopping Bot (Graceful Shutdown)...")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        if not TELEGRAM_TOKEN:
            print("⚠️ Telegram Token not found. Telegram Bot disabled.")
            return

        self.app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("stop", self.stop))

        print("🤖 Telegram Bot Started")
        self.app.run_polling()

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

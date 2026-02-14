from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.interfaces.api import routes
from src.application.bot import TradingBot
import threading

app = FastAPI(
    title="OKX Trading Bot SaaS API",
    description="""
    ## 🚀 SaaS Trading Bot API
    Control your AI trading bot remotely.

    ### Features
    - **Auth**: JWT based security.
    - **Control**: Start/Stop the trading engine.
    - **Data**: Real-time access to trades and equity.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (Allow all for SaaS frontend dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Bot
bot = TradingBot()
# Update the dependency in routes
routes.bot_instance = bot

# Include Routes
app.include_router(routes.router)


@app.on_event("startup")
async def startup_event():
    print("🚀 API Server Starting...")
    from src.config.settings import AUTO_START_BOT
    if AUTO_START_BOT:
        print("🤖 AUTO_START_BOT is True. Starting Bot...")
        bot.start()


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 API Server Shutting Down...")
    bot.stop()

if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)

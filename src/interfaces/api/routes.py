from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from typing import Optional
from src.interfaces.api.auth import Token, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from src.infrastructure.persistence.postgres_repo import PostgresRepository, User
from src.application.bot import TradingBot

router = APIRouter()

# Dependency to get Repos


def get_repo():
    return PostgresRepository()

# Global Bot Instance (injected strictly speaking, but simpler here)
# We will rely on app.state or a global variable set in api.py
# For now, we will assume it is passed or imported.
# ACTUALLY: Let's make it a dependency.


bot_instance = None  # Will be set by api.py


def get_bot():
    if bot_instance is None:
        raise HTTPException(status_code=500, detail="Bot not initialized")
    return bot_instance


def get_cutoff_date(timeframe: str) -> Optional[str]:
    now = datetime.utcnow()
    if timeframe == 'daily':
        return (now - timedelta(days=1)).isoformat()
    elif timeframe == 'weekly':
        return (now - timedelta(weeks=1)).isoformat()
    elif timeframe == 'monthly':
        return (now - timedelta(days=30)).isoformat()
    return None


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    repo = get_repo()
    if not repo.verify_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/bot/status")
async def get_bot_status(current_user: User = Depends(get_current_user), bot: TradingBot = Depends(get_bot)):
    return bot.get_status()


@router.post("/bot/start")
async def start_bot(current_user: User = Depends(get_current_user), bot: TradingBot = Depends(get_bot)):
    bot.start()
    return {"status": "started", "message": "Bot background thread started"}


@router.post("/bot/stop")
async def stop_bot(current_user: User = Depends(get_current_user), bot: TradingBot = Depends(get_bot)):
    bot.stop()
    return {"status": "stopped", "message": "Bot stopping..."}


@router.get("/trades/active")
async def get_active_trades(current_user: User = Depends(get_current_user), repo: PostgresRepository = Depends(get_repo), bot: TradingBot = Depends(get_bot)):
    # Try to get real-time state from Bot memory if running
    if bot and hasattr(bot, 'manager') and bot.manager:
        return bot.manager.state.get("trades", {})

    # Fallback to DB/Repo
    return repo.load_trades()


@router.get("/trades/history")
async def get_trade_history(
    timeframe: str = Query("all", regex="^(daily|weekly|monthly|all)$"),
    current_user: User = Depends(get_current_user),
    repo: PostgresRepository = Depends(get_repo)
):
    start_date = get_cutoff_date(timeframe)
    return repo.load_equity_history(start_date)


@router.get("/trades/closed")
async def get_closed_trades(
    timeframe: str = Query("all", regex="^(daily|weekly|monthly|all)$"),
    current_user: User = Depends(get_current_user),
    repo: PostgresRepository = Depends(get_repo)
):
    start_date = get_cutoff_date(timeframe)
    return repo.load_closed_trades(start_date)


@router.get("/stats/performance")
async def get_performance_stats(
    timeframe: str = Query("all", regex="^(daily|weekly|monthly|all)$"),
    current_user: User = Depends(get_current_user),
    repo: PostgresRepository = Depends(get_repo)
):
    # 1. Fetch Data
    start_date = get_cutoff_date(timeframe)

    closed_trades = repo.load_closed_trades(start_date)
    equity_history = repo.load_equity_history(start_date)

    # 2. Basic Metrics Calculation
    total_closed = len(closed_trades)
    wins = [t for t in closed_trades if t['pnl'] is not None and t['pnl'] > 0]
    losses = [t for t in closed_trades if t['pnl']
              is not None and t['pnl'] <= 0]

    # Recalculate metrics based on filtered data
    total_pnl = sum(t['pnl'] for t in closed_trades if t['pnl'] is not None)

    win_rate = (len(wins) / total_closed * 100) if total_closed > 0 else 0.0

    gross_profit = sum(t['pnl'] for t in wins if t['pnl'] is not None)
    gross_loss = abs(sum(t['pnl'] for t in losses if t['pnl'] is not None))
    profit_factor = (
        gross_profit / gross_loss) if gross_loss > 0 else gross_profit

    # 3. Max Drawdown Calculation
    max_drawdown = 0.0
    if equity_history:
        peak = -float('inf')
        drawdowns = []
        for entry in equity_history:
            equity = entry['equity']
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak if peak > 0 else 0.0
            drawdowns.append(drawdown)
        max_drawdown = max(drawdowns) * 100 if drawdowns else 0.0

    # Filter for Week/Month
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    weekly_pnl = sum(t['pnl'] for t in closed_trades
                     if t['closed_at'] and datetime.fromisoformat(t['closed_at']) >= week_ago and t['pnl'])
    monthly_pnl = sum(t['pnl'] for t in closed_trades
                      if t['closed_at'] and datetime.fromisoformat(t['closed_at']) >= month_ago and t['pnl'])

    # 4. Averages and Current State
    avg_win = (sum(t['pnl'] for t in wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(t['pnl'] for t in losses) / len(losses)) if losses else 0.0

    current_equity = 0.0
    current_balance = 0.0
    if equity_history:
        last_entry = equity_history[-1]
        current_equity = last_entry['equity']
        current_balance = last_entry['balance']

    return {
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "total_trades": total_closed,
        "wins": len(wins),
        "losses": len(losses),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "current_equity": current_equity,
        "current_balance": current_balance
    }

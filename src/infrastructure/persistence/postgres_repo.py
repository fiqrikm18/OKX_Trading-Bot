from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config.settings import DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT
import json
from datetime import datetime

Base = declarative_base()


class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    side = Column(String)
    entry = Column(Float)
    amount = Column(Float)
    margin = Column(Float)
    best_price = Column(Float)
    atr = Column(Float)
    breakeven_active = Column(Boolean)
    dca_count = Column(Integer, default=0)
    status = Column(String, default="OPEN")
    created_at = Column(String, default=datetime.utcnow().isoformat)
    closed_at = Column(String, nullable=True)
    pnl = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)


class BotState(Base):
    __tablename__ = 'bot_state'
    key = Column(String, primary_key=True)
    value = Column(JSON)


class EquityHistory(Base):
    __tablename__ = 'equity_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String)
    balance = Column(Float)
    equity = Column(Float)
    total_pnl = Column(Float)


class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    password_hash = Column(String)


class PostgresRepository:
    def __init__(self):
        self.engine = create_engine(
            f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

        # Schema Migration
        try:
            from sqlalchemy import text, inspect
            with self.engine.connect() as conn:
                # Check if 'id' column exists in trades
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='trades' AND column_name='id'"))
                if not result.fetchone():
                    print(
                        "⚠️ Migrating 'trades' table: Adding 'id' column and updating Primary Key...")
                    # 1. Drop existing primary key (symbol)
                    # Note: Constraint name is usually trades_pkey but good to be sure.
                    conn.execute(
                        text("ALTER TABLE trades DROP CONSTRAINT IF EXISTS trades_pkey"))
                    # 2. Add id column as SERIAL PRIMARY KEY
                    conn.execute(
                        text("ALTER TABLE trades ADD COLUMN id SERIAL PRIMARY KEY"))
                    conn.commit()
                    print("✅ Migration: 'trades' table updated.")

                # Other column checks (idempotent)
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS dca_count INTEGER DEFAULT 0"))
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS created_at VARCHAR"))
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS closed_at VARCHAR"))
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS pnl FLOAT"))
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS exit_reason VARCHAR"))
                conn.commit()
        except Exception as e:
            print(f"Migration Warning: {e}")

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_user(self, username, password):
        import bcrypt
        session = self.Session()
        # Hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

        user = User(username=username, password_hash=hashed.decode('utf-8'))
        session.merge(user)  # Upsert
        session.commit()
        session.close()

    def verify_user(self, username, password):
        import bcrypt
        session = self.Session()
        user = session.query(User).filter_by(username=username).first()
        session.close()

        if not user:
            return False

        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))

    def load_trades(self):
        session = self.Session()
        trades = session.query(Trade).filter_by(status='OPEN').all()
        result = {}
        for t in trades:
            result[t.symbol] = {
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "amount": t.amount,
                "margin": t.margin,
                "best_price": t.best_price,
                "atr": t.atr,
                "breakeven_active": t.breakeven_active,
                "dca_count": t.dca_count,
                "current_price": t.entry,  # Fallback
                "unrealized_pnl": 0.0     # Fallback
            }
        session.close()
        return result

    def save_trade(self, trade_data):
        session = self.Session()
        # Look for EXISTING OPEN trade for this symbol to update
        # If no OPEN trade exists, we create a new row (History preservation)
        trade = session.query(Trade).filter_by(
            symbol=trade_data['symbol'], status='OPEN').first()

        if not trade:
            trade = Trade(symbol=trade_data['symbol'])
            # Only set created_at for new trades
            if 'created_at' in trade_data:
                trade.created_at = trade_data['created_at']
            else:
                trade.created_at = datetime.utcnow().isoformat()

        trade.side = trade_data['side']
        trade.entry = float(trade_data['entry'])
        trade.amount = float(trade_data['amount'])
        trade.margin = float(trade_data.get('margin', 0))
        trade.best_price = float(trade_data.get(
            'best_price', trade_data['entry']))
        trade.atr = float(trade_data.get('atr', 0))
        trade.breakeven_active = bool(
            trade_data.get('breakeven_active', False))
        trade.dca_count = int(trade_data.get('dca_count', 0))
        trade.status = 'OPEN'

        session.add(trade)
        session.commit()
        session.close()

    def close_trade(self, symbol, pnl, exit_reason):
        session = self.Session()
        trade = session.query(Trade).filter_by(symbol=symbol).first()
        if trade:
            trade.status = 'CLOSED'
            trade.pnl = float(pnl)
            trade.exit_reason = str(exit_reason)
            trade.closed_at = datetime.utcnow().isoformat()
            session.commit()
        session.close()

    def load_closed_trades(self, start_date=None):
        session = self.Session()
        query = session.query(Trade).filter_by(status='CLOSED')
        if start_date:
            from sqlalchemy import and_
            # closed_at is ISO string, so lexicographical comparison works for standard ISO8601
            query = query.filter(Trade.closed_at >= start_date)

        trades = query.all()
        result = []
        for t in trades:
            result.append({
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "amount": t.amount,
                "margin": t.margin,
                "pnl": t.pnl,
                "exit_reason": t.exit_reason,
                "created_at": t.created_at,
                "closed_at": t.closed_at
            })
        session.close()
        return result

    def load_state_value(self, key, default=None):
        session = self.Session()
        item = session.query(BotState).filter_by(key=key).first()
        session.close()
        return item.value if item else default

    def save_state_value(self, key, value):
        session = self.Session()
        item = session.query(BotState).filter_by(key=key).first()
        if not item:
            item = BotState(key=key)
        item.value = value
        session.add(item)
        session.commit()
        session.close()

    def log_equity(self, balance, equity, total_pnl):
        session = self.Session()
        entry = EquityHistory(
            timestamp=datetime.utcnow().isoformat(),
            balance=balance,
            equity=equity,
            total_pnl=total_pnl
        )
        session.add(entry)
        session.commit()
        session.close()

    def load_equity_history(self, start_date=None):
        session = self.Session()
        query = session.query(EquityHistory)
        if start_date:
            query = query.filter(EquityHistory.timestamp >= start_date)

        history = query.all()
        result = []
        for h in history:
            result.append({
                "timestamp": h.timestamp,
                "balance": h.balance,
                "equity": h.equity,
                "total_pnl": h.total_pnl
            })
        session.close()
        return result

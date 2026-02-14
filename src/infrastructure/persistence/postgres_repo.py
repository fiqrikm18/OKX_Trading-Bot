from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config.settings import DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT
import json
from datetime import datetime

Base = declarative_base()


class Trade(Base):
    __tablename__ = 'trades'
    symbol = Column(String, primary_key=True)
    side = Column(String)
    entry = Column(Float)
    amount = Column(Float)
    margin = Column(Float)
    best_price = Column(Float)
    atr = Column(Float)
    breakeven_active = Column(Boolean)
    dca_count = Column(Integer, default=0)
    status = Column(String, default="OPEN")


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
        Base.metadata.create_all(self.engine)

        # Schema Migration for dca_count
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE trades ADD COLUMN IF NOT EXISTS dca_count INTEGER DEFAULT 0"))
                conn.commit()
        except Exception as e:
            print(f"Migration Warning: {e}")

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
                "dca_count": t.dca_count
            }
        session.close()
        return result

    def save_trade(self, trade_data):
        session = self.Session()
        trade = session.query(Trade).filter_by(
            symbol=trade_data['symbol']).first()
        if not trade:
            trade = Trade(symbol=trade_data['symbol'])

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

    def close_trade(self, symbol):
        session = self.Session()
        trade = session.query(Trade).filter_by(symbol=symbol).first()
        if trade:
            trade.status = 'CLOSED'
            session.commit()
        session.close()  # Keep in history but mark closed

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

    def load_equity_history(self):
        session = self.Session()
        history = session.query(EquityHistory).all()
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

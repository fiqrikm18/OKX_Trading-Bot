import ccxt
from src.config.settings import API_KEY, SECRET_KEY, PASSWORD, LEVERAGE, REAL_TRADING


class ExchangeClient:
    def __init__(self):
        self.client = ccxt.okx(
            {
                "apiKey": API_KEY,
                "secret": SECRET_KEY,
                "password": PASSWORD,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }
        )

    def fetch_balance(self):
        try:
            balance = self.client.fetch_balance()
            return float(balance["USDT"]["free"])
        except:
            return 0.0

    def set_leverage(self, symbol):
        try:
            self.client.set_margin_mode("isolated", symbol)
            self.client.set_leverage(LEVERAGE, symbol)
        except:
            pass

    def fetch_ohlcv(self, symbol, timeframe, limit):
        return self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_tickers(self):
        return self.client.fetch_tickers()

    def fetch_ticker(self, symbol):
        return self.client.fetch_ticker(symbol)

    def fetch_funding_rate(self, symbol):
        return self.client.fetch_funding_rate(symbol)

    def create_market_buy_order(self, symbol, amount):
        if REAL_TRADING:
            return self.client.create_market_buy_order(symbol, amount)

    def create_market_sell_order(self, symbol, amount):
        if REAL_TRADING:
            return self.client.create_market_sell_order(symbol, amount)


exchange_client = ExchangeClient()

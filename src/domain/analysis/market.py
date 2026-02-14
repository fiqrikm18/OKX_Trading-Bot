import pandas as pd
import pandas_ta as ta
from src.config.settings import TIMEFRAME
from src.infrastructure.exchange.client import exchange_client


def fetch_data(symbol, limit=100):
    try:
        bars = exchange_client.fetch_ohlcv(
            symbol, timeframe=TIMEFRAME, limit=limit)
        df = pd.DataFrame(
            bars, columns=["timestamp", "open",
                           "high", "low", "close", "volume"]
        )

        # Funding Rate
        try:
            funding = exchange_client.fetch_funding_rate(symbol)
            funding_rate = float(funding.get('fundingRate', 0.0))
        except:
            funding_rate = 0.0

        df['Funding'] = funding_rate
        return df
    except:
        return None


def get_market_regime():
    try:
        # Fetch daily candles for BTC for 200 EMA
        btc_bars = exchange_client.fetch_ohlcv(
            "BTC/USDT:USDT", timeframe="1d", limit=205)
        if not btc_bars or len(btc_bars) < 200:
            return "NEUTRAL"

        df = pd.DataFrame(btc_bars, columns=[
                          "timestamp", "open", "high", "low", "close", "volume"])
        df["EMA_200"] = ta.ema(df["close"], length=200)

        last_close = df["close"].iloc[-1]
        last_ema = df["EMA_200"].iloc[-1]

        if last_close > last_ema:
            return "BULL"
        else:
            return "BEAR"
    except Exception as e:
        print(f"Error fetching regime: {e}")
        return "NEUTRAL"


def get_dynamic_symbols(limit=10):
    try:
        tickers = exchange_client.fetch_tickers()
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
                                abs(data["percentage"]
                                    ) if data["percentage"] else 0
                            ),
                        }
                    )
        if not valid_pairs:
            return ["BTC/USDT:USDT", "ETH/USDT:USDT"]
        sorted_pairs = sorted(
            valid_pairs, key=lambda x: x["change"], reverse=True)
        return [item["symbol"] for item in sorted_pairs[:limit]]
    except:
        return ["BTC/USDT:USDT"]

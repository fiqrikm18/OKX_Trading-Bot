import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from src.config.settings import CONFIDENCE_THRESHOLD


def get_ai_signal(df):
    df["RSI"] = ta.rsi(df["close"], length=14)
    df["SMA"] = ta.sma(df["close"], length=20)
    df["ATR"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    df["Returns"] = df["close"].pct_change()
    df["Vol_Change"] = df["volume"].pct_change()
    df["Target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    df.dropna(inplace=True)
    if len(df) < 50:
        return "NEUTRAL", 0.0, 0.0

    features = ["RSI", "SMA", "Returns", "Vol_Change", "Funding"]
    model = RandomForestClassifier(
        n_estimators=100, min_samples_split=10, random_state=42
    )
    model.fit(df[features][:-1], df["Target"][:-1])
    latest = df[features].iloc[[-1]]
    latest_atr = df["ATR"].iloc[-1]
    prob_up = model.predict_proba(latest)[0][1]

    if prob_up > CONFIDENCE_THRESHOLD:
        return "LONG", prob_up, latest_atr
    elif prob_up < (1 - CONFIDENCE_THRESHOLD):
        return "SHORT", (1 - prob_up), latest_atr
    return "NEUTRAL", 0.0, 0.0

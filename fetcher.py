"""
Data fetcher - retrieves stock prices and news via yfinance (free, ~15-min delayed).
"""

import logging
from datetime import datetime

import pandas as pd
import pytz
import yfinance as yf

logger = logging.getLogger(__name__)
ET = pytz.timezone("America/New_York")


def get_market_status() -> dict:
    """
    Returns a dict describing the current market session.
    Keys: status (str), label (str), color (str for Rich).
    """
    now_et = datetime.now(ET)
    weekday = now_et.weekday()  # 0=Monday, 6=Sunday

    if weekday >= 5:
        return {"status": "CLOSED", "label": "Weekend - Closed", "color": "red"}

    mins = now_et.hour * 60 + now_et.minute

    PRE_OPEN  = 4  * 60          # 4:00 AM ET
    OPEN      = 9  * 60 + 30     # 9:30 AM ET
    CLOSE     = 16 * 60          # 4:00 PM ET
    AH_CLOSE  = 20 * 60          # 8:00 PM ET

    if mins < PRE_OPEN:
        return {"status": "CLOSED",      "label": "Closed",       "color": "red"}
    if mins < OPEN:
        return {"status": "PRE_MARKET",  "label": "Pre-Market",   "color": "yellow"}
    if mins < CLOSE:
        return {"status": "OPEN",        "label": "Market OPEN",  "color": "green"}
    if mins < AH_CLOSE:
        return {"status": "AFTER_HOURS", "label": "After Hours",  "color": "yellow"}
    return {"status": "CLOSED", "label": "Closed", "color": "red"}


def fetch_stock(ticker: str, period: str, interval: str) -> tuple:
    """
    Fetch OHLCV history + basic price info for one ticker.
    Returns (DataFrame, info_dict) or (None, None) on failure.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval, auto_adjust=True)

        if df is None or df.empty:
            logger.warning("No data for %s", ticker)
            return None, None

        info: dict = {}
        try:
            fi = stock.fast_info
            info["current_price"] = float(getattr(fi, "last_price",  df["Close"].iloc[-1]))
            info["prev_close"]    = float(getattr(fi, "previous_close", df["Close"].iloc[-2] if len(df) > 1 else df["Close"].iloc[-1]))
            info["volume"]        = int(getattr(fi,   "last_volume",  df["Volume"].iloc[-1]))
            info["avg_volume"]    = float(getattr(fi, "three_month_average_volume", df["Volume"].mean()))
            info["year_high"]     = float(getattr(fi, "year_high",    df["High"].max()))
            info["year_low"]      = float(getattr(fi, "year_low",     df["Low"].min()))
        except Exception:
            close = df["Close"]
            info["current_price"] = float(close.iloc[-1])
            info["prev_close"]    = float(close.iloc[-2] if len(df) > 1 else close.iloc[-1])
            info["volume"]        = int(df["Volume"].iloc[-1])
            info["avg_volume"]    = float(df["Volume"].mean())
            info["year_high"]     = float(df["High"].max())
            info["year_low"]      = float(df["Low"].min())

        return df, info

    except Exception as exc:
        logger.error("Error fetching %s: %s", ticker, exc)
        return None, None


def fetch_news(ticker: str, max_items: int = 5) -> list:
    """
    Fetch recent news headlines for a ticker via yfinance.
    Returns list of dicts with keys: title, publisher, time.
    """
    try:
        items = yf.Ticker(ticker).news or []
        result = []
        for item in items[:max_items]:
            ts = item.get("providerPublishTime") or item.get("providerPublishTime", 0)
            try:
                time_str = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?"
            except Exception:
                time_str = "?"
            result.append({
                "title":     item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "time":      time_str,
            })
        return result
    except Exception:
        return []


def fetch_all(tickers: list, period: str, interval: str) -> dict:
    """
    Fetch data for every ticker in the watchlist.
    Returns {ticker: {"df": df, "info": info, "news": [...]}}
    """
    results = {}
    for ticker in tickers:
        df, info = fetch_stock(ticker, period, interval)
        if df is not None:
            results[ticker] = {
                "df":   df,
                "info": info,
                "news": fetch_news(ticker),
            }
    return results

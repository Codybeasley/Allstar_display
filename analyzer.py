"""
Technical analysis engine.

Computes RSI, MACD, Bollinger Bands, EMA trend, and volume pressure,
then combines them into a single scored signal with entry/stop/target levels.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal types
# ---------------------------------------------------------------------------

class Signal(Enum):
    STRONG_BUY  = "STRONG BUY"
    BUY         = "BUY"
    HOLD        = "HOLD"
    SELL        = "SELL"
    STRONG_SELL = "STRONG SELL"


SIGNAL_COLOR = {
    Signal.STRONG_BUY:  "bright_green",
    Signal.BUY:         "green",
    Signal.HOLD:        "yellow",
    Signal.SELL:        "red",
    Signal.STRONG_SELL: "bright_red",
}

SIGNAL_ICON = {
    Signal.STRONG_BUY:  "▲▲",
    Signal.BUY:         "▲",
    Signal.HOLD:        "─",
    Signal.SELL:        "▼",
    Signal.STRONG_SELL: "▼▼",
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class StockAnalysis:
    ticker: str

    # Price
    price: float
    prev_close: float
    change: float
    change_pct: float

    # Volume
    volume: int
    avg_volume: int
    volume_ratio: float

    # Indicators (None if not enough data)
    rsi:              Optional[float]
    macd:             Optional[float]
    macd_signal_line: Optional[float]
    macd_hist:        Optional[float]
    bb_upper:         Optional[float]
    bb_middle:        Optional[float]
    bb_lower:         Optional[float]
    bb_pct:           Optional[float]   # 0.0 = at lower band, 1.0 = at upper band
    ema_short:        Optional[float]
    ema_medium:       Optional[float]
    ema_long:         Optional[float]
    atr:              Optional[float]
    support:          Optional[float]
    resistance:       Optional[float]

    # Signal
    signal:          Signal
    signal_score:    int                # raw score, roughly -10 to +10
    signal_strength: int                # 0-100 (absolute value scaled)
    reasons: list = field(default_factory=list)  # [(indicator, score, description), ...]

    # Trade plan (populated for BUY / SELL signals only)
    entry_price:   Optional[float] = None
    stop_loss:     Optional[float] = None
    target_price:  Optional[float] = None
    position_size: Optional[int]   = None  # shares
    risk_amount:   Optional[float] = None  # dollars at risk

    # News headlines
    news: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Indicator computation
# ---------------------------------------------------------------------------

def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicator columns to a copy of the OHLCV DataFrame."""
    df = df.copy()
    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # -- RSI --
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=config.RSI_PERIOD - 1, min_periods=config.RSI_PERIOD).mean()
    avg_loss = loss.ewm(com=config.RSI_PERIOD - 1, min_periods=config.RSI_PERIOD).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # -- MACD --
    ema_fast         = close.ewm(span=config.MACD_FAST,   adjust=False).mean()
    ema_slow         = close.ewm(span=config.MACD_SLOW,   adjust=False).mean()
    df["MACD"]       = ema_fast - ema_slow
    df["MACD_Sig"]   = df["MACD"].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
    df["MACD_Hist"]  = df["MACD"] - df["MACD_Sig"]

    # -- Bollinger Bands --
    df["BB_Mid"]    = close.rolling(config.BB_PERIOD).mean()
    bb_std          = close.rolling(config.BB_PERIOD).std()
    df["BB_Upper"]  = df["BB_Mid"] + config.BB_STD * bb_std
    df["BB_Lower"]  = df["BB_Mid"] - config.BB_STD * bb_std
    band_width      = df["BB_Upper"] - df["BB_Lower"]
    df["BB_Pct"]    = (close - df["BB_Lower"]) / band_width.replace(0, np.nan)

    # -- EMAs --
    df["EMA_S"] = close.ewm(span=config.EMA_SHORT,  adjust=False).mean()
    df["EMA_M"] = close.ewm(span=config.EMA_MEDIUM, adjust=False).mean()
    df["EMA_L"] = close.ewm(span=config.EMA_LONG,   adjust=False).mean()

    # -- ATR --
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    df["ATR"] = tr.ewm(com=config.ATR_PERIOD - 1, min_periods=config.ATR_PERIOD).mean()

    # -- Volume MA --
    df["Vol_MA"] = volume.rolling(20).mean()

    # -- Support / Resistance (rolling 50-bar window) --
    lb = min(50, len(df))
    df["Support"]    = low.rolling(lb).min()
    df["Resistance"] = high.rolling(lb).max()

    return df


# ---------------------------------------------------------------------------
# Individual indicator scorers  (each returns (score: int, reason: str))
# score range: -2 to +2
# ---------------------------------------------------------------------------

def _score_rsi(rsi: float):
    if   rsi <= 20: return  2, f"RSI {rsi:.1f} – extremely oversold (strong buy zone)"
    elif rsi <= 30: return  2, f"RSI {rsi:.1f} – oversold (buy signal)"
    elif rsi <= 40: return  1, f"RSI {rsi:.1f} – approaching oversold"
    elif rsi >= 80: return -2, f"RSI {rsi:.1f} – extremely overbought (strong sell zone)"
    elif rsi >= 70: return -2, f"RSI {rsi:.1f} – overbought (sell signal)"
    elif rsi >= 60: return -1, f"RSI {rsi:.1f} – approaching overbought"
    return 0, f"RSI {rsi:.1f} – neutral"


def _score_macd(hist: float, prev_hist: float):
    if   prev_hist <= 0 < hist:        return  2, "MACD bullish crossover (momentum turning up)"
    elif prev_hist >= 0 > hist:        return -2, "MACD bearish crossover (momentum turning down)"
    elif hist > 0 and abs(hist) > 0:   return  1, "MACD above signal line (bullish momentum)"
    elif hist < 0 and abs(hist) > 0:   return -1, "MACD below signal line (bearish momentum)"
    return 0, "MACD neutral"


def _score_bb(bb_pct: float):
    if   bb_pct <= 0.0:  return  2, "Price below lower Bollinger Band (oversold bounce setup)"
    elif bb_pct <= 0.15: return  2, "Price near lower Bollinger Band (buy zone)"
    elif bb_pct <= 0.30: return  1, "Price in lower Bollinger zone (mild bullish)"
    elif bb_pct >= 1.0:  return -2, "Price above upper Bollinger Band (overbought reversal risk)"
    elif bb_pct >= 0.85: return -2, "Price near upper Bollinger Band (sell zone)"
    elif bb_pct >= 0.70: return -1, "Price in upper Bollinger zone (mild bearish)"
    return 0, "Price in middle of Bollinger Bands (neutral)"


def _score_ema(price: float, es: float, em: float, el: float):
    bullish_stack = price > es > em > el
    bearish_stack = price < es < em < el
    above_all  = price > es and price > em and price > el
    below_all  = price < es and price < em and price < el

    if bullish_stack:
        return  2, "Price & all EMAs in bullish stack (strong uptrend)"
    if above_all:
        return  1, "Price above all EMAs (uptrend)"
    if bearish_stack:
        return -2, "Price & all EMAs in bearish stack (strong downtrend)"
    if below_all:
        return -1, "Price below all EMAs (downtrend)"
    return 0, "Mixed EMA alignment (choppy / transitioning)"


def _score_volume(volume: int, avg_volume: float, change_pct: float):
    if avg_volume <= 0:
        return 0, "Volume data unavailable"
    ratio = volume / avg_volume
    if   ratio >= 2.0 and change_pct > 0: return  2, f"Volume {ratio:.1f}x avg on UP move (strong buying pressure)"
    elif ratio >= 1.5 and change_pct > 0: return  1, f"Volume {ratio:.1f}x avg on UP move (buying pressure)"
    elif ratio >= 2.0 and change_pct < 0: return -2, f"Volume {ratio:.1f}x avg on DOWN move (strong selling pressure)"
    elif ratio >= 1.5 and change_pct < 0: return -1, f"Volume {ratio:.1f}x avg on DOWN move (selling pressure)"
    elif ratio < 0.5:                     return  0, f"Low volume ({ratio:.1f}x avg) – weak conviction"
    return 0, f"Normal volume ({ratio:.1f}x avg)"


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return f if not (f != f) else None  # NaN check
    except Exception:
        return None


def analyze_stock(ticker: str, df: pd.DataFrame, info: dict, news: list) -> StockAnalysis:
    df = _compute_indicators(df)
    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) > 1 else latest

    # Current price & change
    price      = info.get("current_price", float(latest["Close"]))
    prev_close = info.get("prev_close",    float(prev["Close"]))
    change     = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0
    volume     = int(info.get("volume",     int(latest["Volume"])))
    avg_volume = float(info.get("avg_volume", float(df["Volume"].mean())))
    vol_ratio  = volume / avg_volume if avg_volume > 0 else 1.0

    # Extract indicator values
    rsi       = _safe_float(latest.get("RSI"))
    macd      = _safe_float(latest.get("MACD"))
    macd_sig  = _safe_float(latest.get("MACD_Sig"))
    macd_hist = _safe_float(latest.get("MACD_Hist"))
    prev_hist = _safe_float(prev.get("MACD_Hist"))
    bb_upper  = _safe_float(latest.get("BB_Upper"))
    bb_middle = _safe_float(latest.get("BB_Mid"))
    bb_lower  = _safe_float(latest.get("BB_Lower"))
    bb_pct    = _safe_float(latest.get("BB_Pct"))
    ema_s     = _safe_float(latest.get("EMA_S"))
    ema_m     = _safe_float(latest.get("EMA_M"))
    ema_l     = _safe_float(latest.get("EMA_L"))
    atr       = _safe_float(latest.get("ATR"))
    support   = _safe_float(latest.get("Support"))
    resistance= _safe_float(latest.get("Resistance"))

    # Score each indicator
    total_score = 0
    reasons     = []

    if rsi is not None:
        s, r = _score_rsi(rsi)
        total_score += s
        if s != 0:
            reasons.append(("RSI", s, r))

    if macd_hist is not None and prev_hist is not None:
        s, r = _score_macd(macd_hist, prev_hist)
        total_score += s
        if s != 0:
            reasons.append(("MACD", s, r))

    if bb_pct is not None:
        s, r = _score_bb(bb_pct)
        total_score += s
        if s != 0:
            reasons.append(("BB", s, r))

    if all(v is not None for v in [ema_s, ema_m, ema_l]):
        s, r = _score_ema(price, ema_s, ema_m, ema_l)
        total_score += s
        if s != 0:
            reasons.append(("EMA", s, r))

    s, r = _score_volume(volume, avg_volume, change_pct)
    total_score += s
    if s != 0:
        reasons.append(("VOL", s, r))

    # Determine signal from total score
    if   total_score >= 6:  signal = Signal.STRONG_BUY
    elif total_score >= 3:  signal = Signal.BUY
    elif total_score <= -6: signal = Signal.STRONG_SELL
    elif total_score <= -3: signal = Signal.SELL
    else:                   signal = Signal.HOLD

    signal_strength = min(100, abs(total_score) * 10)

    # Build trade plan for actionable signals
    entry_price = stop_loss = target_price = None
    position_size = risk_amount = None

    if signal in (Signal.BUY, Signal.STRONG_BUY) and atr:
        entry_price   = round(price * 1.001, 2)
        stop_loss     = round(entry_price - atr * config.ATR_MULTIPLIER, 2)
        risk_per_share = entry_price - stop_loss
        if risk_per_share > 0:
            risk_amount   = config.ACCOUNT_BALANCE * config.MAX_RISK_PER_TRADE
            position_size = max(1, int(risk_amount / risk_per_share))
            target_price  = round(entry_price + risk_per_share * config.RISK_REWARD_RATIO, 2)

    elif signal in (Signal.SELL, Signal.STRONG_SELL) and atr:
        entry_price   = round(price * 0.999, 2)
        stop_loss     = round(entry_price + atr * config.ATR_MULTIPLIER, 2)
        risk_per_share = stop_loss - entry_price
        if risk_per_share > 0:
            risk_amount   = config.ACCOUNT_BALANCE * config.MAX_RISK_PER_TRADE
            position_size = max(1, int(risk_amount / risk_per_share))
            target_price  = round(entry_price - risk_per_share * config.RISK_REWARD_RATIO, 2)

    return StockAnalysis(
        ticker=ticker,
        price=price, prev_close=prev_close, change=change, change_pct=change_pct,
        volume=volume, avg_volume=int(avg_volume), volume_ratio=vol_ratio,
        rsi=rsi, macd=macd, macd_signal_line=macd_sig, macd_hist=macd_hist,
        bb_upper=bb_upper, bb_middle=bb_middle, bb_lower=bb_lower, bb_pct=bb_pct,
        ema_short=ema_s, ema_medium=ema_m, ema_long=ema_l,
        atr=atr, support=support, resistance=resistance,
        signal=signal, signal_score=total_score, signal_strength=signal_strength,
        reasons=reasons,
        entry_price=entry_price, stop_loss=stop_loss, target_price=target_price,
        position_size=position_size, risk_amount=risk_amount,
        news=news,
    )


def analyze_all(data: dict) -> list:
    """
    Analyze all tickers.  Returns a list of StockAnalysis sorted by
    signal strength (strongest signals first).
    """
    results = []
    for ticker, stock_data in data.items():
        try:
            a = analyze_stock(
                ticker,
                stock_data["df"],
                stock_data["info"],
                stock_data.get("news", []),
            )
            results.append(a)
        except Exception as exc:
            logger.error("Error analyzing %s: %s", ticker, exc)

    results.sort(key=lambda x: abs(x.signal_score), reverse=True)
    return results

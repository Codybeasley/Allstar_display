"""
Allstar Day Trading Advisor - Configuration
Edit this file to customize your watchlist, account settings, and analysis parameters.
"""

# ============================================================
# WATCHLIST - Stocks to monitor each day
# Add or remove tickers as you like.
# ============================================================
WATCHLIST = [
    # High-volume mega-cap tech (liquid, tight spreads)
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "NVDA",   # Nvidia
    "GOOGL",  # Alphabet
    "AMZN",   # Amazon
    "META",   # Meta
    # Volatile momentum names (larger moves, more opportunity)
    "TSLA",   # Tesla
    "AMD",    # Advanced Micro Devices
    "PLTR",   # Palantir
    # Market pulse ETFs
    "SPY",    # S&P 500
    "QQQ",    # Nasdaq 100
]

# ============================================================
# FIDELITY ACCOUNT SETTINGS
# Update ACCOUNT_BALANCE with your actual Fidelity cash balance.
# The advisor sizes positions so you never risk more than
# MAX_RISK_PER_TRADE of your account on a single trade.
# ============================================================
ACCOUNT_BALANCE = 10000       # Your Fidelity account balance in dollars
MAX_RISK_PER_TRADE = 0.02     # 2% max risk per trade ($200 on a $10k account)
MAX_POSITIONS = 5             # Maximum number of open positions at once

# ============================================================
# TECHNICAL INDICATOR SETTINGS
# These control how signals are calculated. The defaults are
# standard settings used by most professional traders.
# ============================================================

# RSI (Relative Strength Index) - measures overbought/oversold
RSI_PERIOD = 14
RSI_OVERSOLD = 30       # RSI below this = potential buy opportunity
RSI_OVERBOUGHT = 70     # RSI above this = potential sell opportunity

# EMA (Exponential Moving Average) - measures trend direction
EMA_SHORT = 9           # Fast trend (reacts quickly)
EMA_MEDIUM = 21         # Medium trend
EMA_LONG = 50           # Slow trend (big picture)

# MACD - measures momentum and trend changes
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands - measures volatility and price extremes
BB_PERIOD = 20
BB_STD = 2.0

# ATR (Average True Range) - used for stop-loss calculation
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5    # Stop = entry ± (ATR × this value)
RISK_REWARD_RATIO = 2.0 # Target = entry + (risk × this). 2.0 = 2:1 reward-to-risk

# ============================================================
# DATA & UPDATE SETTINGS
# ============================================================
DATA_PERIOD = "5d"      # How much history to load (5 trading days)
DATA_INTERVAL = "5m"    # Candle size: "1m", "5m", "15m", "1h"
UPDATE_INTERVAL = 60    # Refresh data every N seconds (60 = 1 minute)

# ============================================================
# DISPLAY SETTINGS
# ============================================================
SHOW_ONLY_ACTIONABLE = False  # True = hide HOLD signals, show only BUY/SELL
MIN_SIGNAL_STRENGTH = 0       # Minimum signal strength to display (0-100)
MAX_NEWS_ITEMS = 8            # Max total news items shown in the news panel

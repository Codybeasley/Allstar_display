# Allstar Day Trading Advisor

A live terminal dashboard that monitors your stock watchlist and tells you **when to buy and when to sell** — updated every 60 seconds throughout the trading day.

> **DISCLAIMER:** This tool is for educational and informational purposes only. It does not constitute financial advice. Day trading involves substantial risk of loss. Always do your own research before placing any trade.

---

## What It Does

- Watches a configurable list of stocks (default: AAPL, MSFT, NVDA, TSLA, SPY, QQQ, and more)
- Calculates **5 technical indicators** for each stock every minute:
  - **RSI** – identifies oversold (buy) and overbought (sell) conditions
  - **MACD** – detects momentum shifts and trend crossovers
  - **Bollinger Bands** – spots price extremes and potential reversals
  - **EMA Trend** – confirms the overall direction (up or down)
  - **Volume** – validates whether a move has real buying/selling pressure
- Combines them into a single signal: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL**
- For BUY and SELL signals, gives you:
  - **Entry price** – where to place your order
  - **Stop-loss** – where to cut the loss if wrong
  - **Target price** – where to take profit
  - **Number of shares** – sized so you never risk more than 2% of your account
- Shows the top 3 actionable signals with full reasoning
- Displays recent news headlines for each stock
- Knows market hours (pre-market, regular, after-hours, closed)

---

## Setup

### Requirements
- Python 3.9 or later
- A terminal at least 120 columns wide (fullscreen recommended)

### Install

```bash
# 1. Clone or navigate to the project folder
cd Allstar_display

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set your Fidelity account balance in config.py
#    Open config.py and change:
#       ACCOUNT_BALANCE = 10000
#    to your actual cash balance so position sizes are accurate.

# 4. Run the advisor
python main.py
```

Press **Ctrl+C** to exit cleanly.

---

## Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `WATCHLIST` | 11 stocks | Tickers to monitor |
| `ACCOUNT_BALANCE` | `10000` | Your Fidelity account balance |
| `MAX_RISK_PER_TRADE` | `0.02` | Max risk per trade (2% of balance) |
| `MAX_POSITIONS` | `5` | Max open positions at once |
| `DATA_INTERVAL` | `"5m"` | Candle size (`"1m"`, `"5m"`, `"15m"`) |
| `UPDATE_INTERVAL` | `60` | Seconds between data refreshes |
| `SHOW_ONLY_ACTIONABLE` | `False` | Hide HOLD signals |

---

## How to Use With Fidelity

1. **Run the advisor** and watch for **STRONG BUY** or **BUY** signals (green arrows ▲▲ or ▲).
2. **Check the "Top Actionable Signals" panel** — it shows:
   - Entry price, stop-loss, target, shares to buy, and total cost
3. **Log in to Fidelity** (fidelity.com or the app) and place a **limit order** at the entry price.
4. **Immediately set a stop-loss order** at the stop price shown. This protects you if the trade goes wrong.
5. **Exit when the target price is hit** or when the signal flips to SELL/HOLD.

> **Note:** Stock data from yfinance is approximately 15 minutes delayed for free. Always confirm the current price in Fidelity before placing an order.

---

## Signal Scoring

Each indicator contributes a score from -2 to +2:

| Score | RSI | MACD | Bollinger | EMA | Volume |
|---|---|---|---|---|---|
| +2 | ≤ 30 (oversold) | Bullish crossover | Below lower band | Full bullish stack | 2×+ avg on up move |
| +1 | 30–40 | Above signal line | Near lower band | Above all EMAs | 1.5×+ avg on up move |
|  0 | 40–60 | Neutral | Middle | Mixed | Normal |
| -1 | 60–70 | Below signal line | Near upper band | Below all EMAs | 1.5×+ avg on down move |
| -2 | ≥ 70 (overbought) | Bearish crossover | Above upper band | Full bearish stack | 2×+ avg on down move |

**Total score → Signal:**
- ≥ +6 → STRONG BUY
- +3 to +5 → BUY
- -2 to +2 → HOLD
- -3 to -5 → SELL
- ≤ -6 → STRONG SELL

---

## Important Warnings

- **Day trading is risky.** Studies show that 70–90% of day traders lose money over time.
- **This is not financial advice.** The signals are based on historical patterns that do not guarantee future results.
- **Start small.** If you're new to trading, consider paper-trading (simulated trades) before using real money.
- **Fidelity has no public API.** All trades must be placed manually in your Fidelity account — this tool is advisory only.
- **Data is delayed ~15 minutes** on the free yfinance feed. For true real-time data, consider a paid provider like Polygon.io.

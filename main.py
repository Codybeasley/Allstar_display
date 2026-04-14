#!/usr/bin/env python3
"""
Allstar Day Trading Advisor
===========================
Monitors your watchlist every 60 seconds and displays buy/sell signals
based on RSI, MACD, Bollinger Bands, EMA trend, and volume analysis.

Usage:
    python main.py

Press Ctrl+C to exit.
"""

import logging
import time
from datetime import datetime

from rich.live import Live
from rich.panel import Panel
from rich.text import Text

import config
import display
from analyzer import analyze_all
from display import console
from fetcher import fetch_all, get_market_status

# Log warnings and errors to a file so they don't clutter the screen
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s  %(levelname)s  %(name)s: %(message)s",
    handlers=[logging.FileHandler("trading_advisor.log", encoding="utf-8")],
)


def _startup_screen():
    console.clear()
    t = Text(justify="center")
    t.append("\n")
    t.append("  ALLSTAR DAY TRADING ADVISOR  \n", style="bold white on blue")
    t.append("\n")
    t.append("Loading market data for your watchlist…\n", style="dim")
    t.append(f"Tracking: {', '.join(config.WATCHLIST)}\n", style="cyan")
    t.append("\n")
    t.append("This may take 10–20 seconds on first run.\n", style="dim")
    console.print(Panel(t, border_style="blue"))


def main():
    _startup_screen()

    # -----------------------------------------------------------------------
    # Initial data load
    # -----------------------------------------------------------------------
    data          = fetch_all(config.WATCHLIST, config.DATA_PERIOD, config.DATA_INTERVAL)
    analyses      = analyze_all(data)
    last_updated  = datetime.now()
    market_status = get_market_status()

    tick          = 0  # counts seconds; refresh data every UPDATE_INTERVAL ticks

    # -----------------------------------------------------------------------
    # Live dashboard loop
    # -----------------------------------------------------------------------
    with Live(
        display.render(analyses, market_status, last_updated),
        console=console,
        refresh_per_second=1,
        screen=True,
    ) as live:
        while True:
            try:
                tick += 1

                if tick >= config.UPDATE_INTERVAL:
                    tick          = 0
                    data          = fetch_all(config.WATCHLIST, config.DATA_PERIOD, config.DATA_INTERVAL)
                    analyses      = analyze_all(data)
                    last_updated  = datetime.now()
                    market_status = get_market_status()

                # Redraw every second so the clock stays current
                live.update(display.render(analyses, market_status, last_updated))
                time.sleep(1)

            except KeyboardInterrupt:
                break
            except Exception as exc:
                logging.getLogger(__name__).error("Main loop error: %s", exc)
                time.sleep(5)

    # -----------------------------------------------------------------------
    # Goodbye
    # -----------------------------------------------------------------------
    console.print()
    console.print(Panel(
        "[bold cyan]Allstar Day Trading Advisor stopped.[/bold cyan]\n"
        "[dim]Remember: Only trade with money you can afford to lose.[/dim]",
        border_style="blue",
    ))


if __name__ == "__main__":
    main()

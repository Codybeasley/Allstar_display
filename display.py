"""
Rich terminal dashboard - renders the live trading advisor UI.
"""

from datetime import datetime
from typing import Optional

import pytz
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

import config
from analyzer import Signal, SIGNAL_COLOR, SIGNAL_ICON, StockAnalysis

console = Console()
ET = pytz.timezone("America/New_York")

_DISCLAIMER = (
    "[bold red]DISCLAIMER:[/bold red]  This tool is for [bold]educational and informational purposes only[/bold]. "
    "It does NOT constitute financial advice. Day trading carries [bold red]substantial risk of loss[/bold red] — "
    "the majority of day traders lose money. Never trade money you cannot afford to lose. "
    "Always do your own research before placing any trade."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fp(price: float, decimals: int = 2) -> str:
    """Format a dollar price."""
    return f"${price:,.{decimals}f}"


def _fvol(vol: int) -> str:
    """Format a volume number compactly."""
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:.1f}M"
    if vol >= 1_000:
        return f"{vol / 1_000:.0f}K"
    return str(vol)


def _change_text(change: float, pct: float) -> Text:
    t = Text()
    arrow = "▲" if change >= 0 else "▼"
    color = "green" if change >= 0 else "red"
    t.append(f"{arrow} {abs(pct):.2f}%", style=color)
    return t


def _strength_bar(strength: int) -> str:
    filled = max(0, min(10, strength // 10))
    return "█" * filled + "░" * (10 - filled)


# ---------------------------------------------------------------------------
# Panel builders
# ---------------------------------------------------------------------------

def _build_header(market_status: dict, last_updated: datetime) -> Panel:
    now_et = datetime.now(ET)
    t = Text(justify="center")
    t.append("  ALLSTAR DAY TRADING ADVISOR  ", style="bold white on blue")
    t.append("   ", style="")
    t.append("Market: ",        style="dim")
    t.append(market_status["label"], style=f"bold {market_status['color']}")
    t.append("   ET: ",         style="dim")
    t.append(now_et.strftime("%I:%M:%S %p"), style="white")
    t.append("   Updated: ",    style="dim")
    t.append(last_updated.strftime("%H:%M:%S"), style="dim")
    t.append("   Account: ",    style="dim")
    t.append(f"${config.ACCOUNT_BALANCE:,.0f}", style="cyan")
    t.append("   Max Risk/Trade: ", style="dim")
    t.append(f"${config.ACCOUNT_BALANCE * config.MAX_RISK_PER_TRADE:,.0f}", style="yellow")
    return Panel(t, style="blue", padding=(0, 0))


def _build_watchlist_table(analyses: list) -> Table:
    tbl = Table(
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        expand=True,
        show_edge=True,
    )
    tbl.add_column("TICKER",   style="bold white",  width=8,  no_wrap=True)
    tbl.add_column("PRICE",    justify="right",      width=10, no_wrap=True)
    tbl.add_column("CHANGE",   justify="right",      width=11, no_wrap=True)
    tbl.add_column("SIGNAL",   justify="center",     width=16, no_wrap=True)
    tbl.add_column("STRENGTH", justify="center",     width=12, no_wrap=True)
    tbl.add_column("RSI",      justify="right",      width=7,  no_wrap=True)
    tbl.add_column("ENTRY",    justify="right",      width=10, no_wrap=True)
    tbl.add_column("STOP",     justify="right",      width=10, no_wrap=True)
    tbl.add_column("TARGET",   justify="right",      width=10, no_wrap=True)
    tbl.add_column("SHARES",   justify="right",      width=8,  no_wrap=True)
    tbl.add_column("VOLUME",   justify="right",      width=9,  no_wrap=True)

    displayed = [
        a for a in analyses
        if not config.SHOW_ONLY_ACTIONABLE or a.signal != Signal.HOLD
    ]

    for a in displayed:
        sc     = SIGNAL_COLOR.get(a.signal, "white")
        si     = SIGNAL_ICON.get(a.signal, "─")
        sig_label = f"{si} {a.signal.value}"

        rsi_str = f"{a.rsi:.1f}" if a.rsi is not None else "─"
        rsi_col = (
            "green" if a.rsi and a.rsi < 30 else
            "red"   if a.rsi and a.rsi > 70 else
            "white"
        )

        entry_str  = _fp(a.entry_price)  if a.entry_price  else "─"
        stop_str   = _fp(a.stop_loss)    if a.stop_loss    else "─"
        target_str = _fp(a.target_price) if a.target_price else "─"
        shares_str = str(a.position_size) if a.position_size else "─"

        tbl.add_row(
            a.ticker,
            _fp(a.price),
            _change_text(a.change, a.change_pct),
            f"[{sc}]{sig_label}[/{sc}]",
            f"[{sc}]{_strength_bar(a.signal_strength)}[/{sc}]",
            f"[{rsi_col}]{rsi_str}[/{rsi_col}]",
            entry_str,
            f"[red]{stop_str}[/red]"     if stop_str   != "─" else "─",
            f"[green]{target_str}[/green]" if target_str != "─" else "─",
            shares_str,
            _fvol(a.volume),
        )

    return tbl


def _build_signals_panel(analyses: list) -> Panel:
    """Detailed breakdown of the top 3 actionable signals."""
    actionable = [
        a for a in analyses
        if a.signal in (Signal.STRONG_BUY, Signal.BUY, Signal.SELL, Signal.STRONG_SELL)
    ][:3]

    if not actionable:
        body = Text("\n  No strong signals right now. Market may be consolidating or data is loading.\n", style="yellow")
        return Panel(body, title="[bold cyan]Top Actionable Signals[/bold cyan]", border_style="cyan")

    body = Text()
    for i, a in enumerate(actionable):
        if i:
            body.append("\n" + "─" * 72 + "\n", style="dim")
        sc = SIGNAL_COLOR.get(a.signal, "white")
        si = SIGNAL_ICON.get(a.signal, "─")

        body.append(f"  {a.ticker}", style="bold white")
        body.append(f"   {si} {a.signal.value}", style=f"bold {sc}")
        body.append(f"   @ {_fp(a.price)}", style="white")
        body.append(f"   Score: {a.signal_score:+d}/10\n", style="dim")

        if a.entry_price and a.stop_loss and a.target_price:
            is_long = a.signal in (Signal.BUY, Signal.STRONG_BUY)
            risk    = abs(a.entry_price - a.stop_loss)
            reward  = abs(a.target_price - a.entry_price)
            rr      = reward / risk if risk else 0

            body.append(f"  Entry: {_fp(a.entry_price)}   ", style="white")
            body.append(f"Stop Loss: {_fp(a.stop_loss)}   ", style="red")
            body.append(f"Target: {_fp(a.target_price)}   ", style="green")
            body.append(f"R:R = {rr:.1f}:1\n",               style="cyan")

            if a.position_size and a.risk_amount:
                cost = a.entry_price * a.position_size
                body.append(f"  Shares: {a.position_size}   ", style="white")
                body.append(f"Risk $: ${a.risk_amount:.0f}   ", style="yellow")
                body.append(f"Total Cost: ${cost:,.0f}\n",      style="white")

            direction = "BUY (long)" if is_long else "SELL SHORT"
            body.append(f"  → Place a {direction} order in Fidelity at or near the entry price.\n", style="dim italic")

        if a.reasons:
            body.append("  Why: ", style="dim")
            parts = []
            for _, score, reason in a.reasons[:4]:
                col = "green" if score > 0 else "red"
                parts.append(f"[{col}]{reason}[/{col}]")
            body.append(" · ".join(parts) + "\n")

        if a.news:
            headline = a.news[0]["title"][:72]
            src      = a.news[0]["publisher"]
            body.append(f"  News: {headline} [{src}]\n", style="dim italic")

    return Panel(body, title="[bold cyan]Top Actionable Signals[/bold cyan]", border_style="cyan", padding=(0, 0))


def _build_news_panel(analyses: list) -> Panel:
    body = Text()
    shown = 0
    for a in analyses:
        for item in a.news[:2]:
            if shown >= config.MAX_NEWS_ITEMS:
                break
            body.append(f"[{a.ticker}] ", style="bold cyan")
            body.append(f"{item['title'][:74]}", style="white")
            body.append(f"  {item['publisher']}  {item['time']}\n", style="dim")
            shown += 1
        if shown >= config.MAX_NEWS_ITEMS:
            break

    if not shown:
        body.append("No recent news available.", style="dim")

    return Panel(body, title="[bold cyan]Recent News[/bold cyan]", border_style="dim blue", padding=(0, 1))


def _build_tips_panel(market_status: dict) -> Panel:
    tips = Text()
    status = market_status["status"]

    if status == "OPEN":
        tips.append("Trading Tips  ", style="bold yellow")
        tips.append(
            "• Only trade STRONG BUY/SELL signals with strength ≥50.  "
            "• Always enter a stop-loss order immediately after buying.  "
            "• Never risk more than 2% of your account on one trade.  "
            "• Data is ~15 min delayed – verify price in Fidelity before ordering.",
            style="dim"
        )
    elif status in ("PRE_MARKET", "AFTER_HOURS"):
        tips.append("Extended Hours  ", style="bold yellow")
        tips.append(
            "• Spreads are wider and liquidity is lower outside regular hours.  "
            "• Use limit orders only.  "
            "• Signals shown are based on last available data.",
            style="dim"
        )
    else:
        tips.append("Market Closed  ", style="bold yellow")
        tips.append(
            "• Review signals and plan your trades for tomorrow's open.  "
            "• Regular market hours: 9:30 AM – 4:00 PM ET, Monday–Friday.  "
            "• Signals update automatically when market reopens.",
            style="dim"
        )

    return Panel(tips, border_style="dim yellow", padding=(0, 1))


# ---------------------------------------------------------------------------
# Full layout assembly
# ---------------------------------------------------------------------------

def render(analyses: list, market_status: dict, last_updated: datetime) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header",     size=3),
        Layout(name="disclaimer", size=3),
        Layout(name="watchlist",  ratio=1),
        Layout(name="signals",    size=14),
        Layout(name="news",       size=11),
        Layout(name="tips",       size=4),
    )

    layout["header"].update(_build_header(market_status, last_updated))
    layout["disclaimer"].update(
        Panel(_DISCLAIMER, border_style="dim red", padding=(0, 1))
    )
    layout["watchlist"].update(
        Panel(
            _build_watchlist_table(analyses),
            title="[bold cyan]Watchlist Analysis[/bold cyan]",
            border_style="blue",
        )
    )
    layout["signals"].update(_build_signals_panel(analyses))
    layout["news"].update(_build_news_panel(analyses))
    layout["tips"].update(_build_tips_panel(market_status))

    return layout

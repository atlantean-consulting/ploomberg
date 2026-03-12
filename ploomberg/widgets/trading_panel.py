"""Paper trading display widget — portfolio summary, positions, trade form, and history."""

from __future__ import annotations

from textual.containers import Container, Horizontal
from textual.widgets import Static, Input, Select
from textual.app import ComposeResult

from ploomberg.config import AVAILABLE_ASSETS
from ploomberg.paper_trading import Portfolio, save_portfolio


def _fmt_usd(value: float) -> str:
    return f"${value:,.2f}"


def _pnl_colored(pnl: float) -> str:
    if pnl > 0:
        return f"[green]+{_fmt_usd(pnl)}[/green]"
    elif pnl < 0:
        return f"[red]{_fmt_usd(pnl)}[/red]"
    return f"[yellow]{_fmt_usd(pnl)}[/yellow]"


def _pct_colored(pct: float) -> str:
    if pct > 0:
        return f"[green]+{pct:.2f}%[/green]"
    elif pct < 0:
        return f"[red]{pct:.2f}%[/red]"
    return f"[yellow]{pct:.2f}%[/yellow]"


class TradingPanel(Container):
    DEFAULT_CSS = """
    TradingPanel {
        height: 1fr;
        width: 100%;
        border: heavy $accent;
        padding: 0 1;
        overflow-y: auto;
    }
    TradingPanel .tp-section-header {
        text-style: bold;
        color: $primary;
        height: 1;
        margin-top: 1;
    }
    TradingPanel .tp-separator {
        height: 1;
        color: $text-muted;
    }
    TradingPanel .tp-row {
        height: 1;
    }
    TradingPanel .tp-empty {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }
    TradingPanel .tp-trade-row {
        height: 1;
    }
    TradingPanel .tp-error {
        height: 1;
        color: $error;
    }
    TradingPanel .tp-success {
        height: 1;
        color: $success;
    }
    TradingPanel .trade-row {
        height: auto;
        layout: horizontal;
        width: 100%;
    }
    TradingPanel .trade-row .trade-label {
        width: 16;
        height: 3;
        padding: 1 1 0 1;
    }
    TradingPanel .trade-row Input {
        width: 24;
        height: 3;
    }
    TradingPanel .trade-row Select {
        width: 28;
    }
    TradingPanel .tp-pos-row {
        height: 1;
    }
    """

    def __init__(self, portfolio: Portfolio, **kwargs) -> None:
        super().__init__(**kwargs)
        self._portfolio = portfolio
        self._prices: dict[str, float] = {}

    def compose(self) -> ComposeResult:
        # --- Portfolio Summary ---
        yield Static("  PORTFOLIO SUMMARY", classes="tp-section-header")
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static("", id="tp-cash", classes="tp-row")
        yield Static("", id="tp-invested", classes="tp-row")
        yield Static("", id="tp-total-value", classes="tp-row")
        yield Static("", id="tp-return", classes="tp-row")

        # --- Positions ---
        yield Static("  OPEN POSITIONS", classes="tp-section-header")
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static(
            f"  {'ASSET':<8} {'QTY':>10} {'AVG COST':>10} {'PRICE':>10} {'VALUE':>12} {'P&L':>14}",
            classes="tp-row",
        )
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static("", id="tp-positions")

        # --- Trade Form ---
        yield Static("  EXECUTE TRADE", classes="tp-section-header")
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static(
            "  Enter ticker OR pick from watchlist, set quantity, then [bold]F9[/] Buy / [bold]F10[/] Sell",
            classes="tp-row",
        )
        watchlist = self._get_watchlist()
        options = [(self._asset_label(a), a) for a in watchlist]
        with Horizontal(classes="trade-row"):
            yield Static("  Ticker:", classes="trade-label")
            yield Input(placeholder="e.g. XAU", id="trade-custom")
        with Horizontal(classes="trade-row"):
            yield Static("  Watchlist:", classes="trade-label")
            yield Select(options, id="trade-asset", prompt="Select…")
        with Horizontal(classes="trade-row"):
            yield Static("  Quantity:", classes="trade-label")
            yield Input(placeholder="e.g. 10", id="trade-qty")
        yield Static("", id="tp-feedback", classes="tp-row")

        # --- Trade History ---
        yield Static("  TRADE HISTORY", classes="tp-section-header")
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static(
            f"  {'TIME':<20} {'SIDE':<5} {'ASSET':<8} {'QTY':>10} {'PRICE':>10} {'TOTAL':>12}",
            classes="tp-row",
        )
        yield Static("  " + "─" * 74, classes="tp-separator")
        yield Static("", id="tp-history")

    def _get_watchlist(self) -> list[str]:
        try:
            return list(self.app.config.watchlist)
        except Exception:
            return list(AVAILABLE_ASSETS.keys())

    def _asset_label(self, asset_id: str) -> str:
        info = AVAILABLE_ASSETS.get(asset_id, {})
        name = info.get("name", asset_id)
        return f"{asset_id} ({name})"

    def on_mount(self) -> None:
        self._refresh_all()

    def update_prices(self, prices: dict[str, float]) -> None:
        """Called with {asset_id: price} when prices update."""
        self._prices.update(prices)
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_summary()
        self._refresh_positions()
        self._refresh_history()

    def _refresh_summary(self) -> None:
        p = self._portfolio
        prices = self._prices

        self.query_one("#tp-cash", Static).update(
            f"  Cash:            {_fmt_usd(p.cash)}"
        )

        invested = p.invested_value(prices)
        self.query_one("#tp-invested", Static).update(
            f"  Invested Value:  {_fmt_usd(invested)}" if prices else
            "  Invested Value:  [dim]waiting for prices…[/dim]"
        )

        if prices:
            total = p.total_value(prices)
            ret = p.total_return(prices)
            ret_pct = p.total_return_pct(prices)
            self.query_one("#tp-total-value", Static).update(
                f"  Total Value:     {_fmt_usd(total)}"
            )
            self.query_one("#tp-return", Static).update(
                f"  Total Return:    {_pnl_colored(ret)}  ({_pct_colored(ret_pct)})"
            )
        else:
            self.query_one("#tp-total-value", Static).update(
                "  Total Value:     [dim]waiting for prices…[/dim]"
            )
            self.query_one("#tp-return", Static).update(
                "  Total Return:    [dim]---[/dim]"
            )

    def _refresh_positions(self) -> None:
        positions = self._portfolio.positions
        if not positions:
            self.query_one("#tp-positions", Static).update(
                "  [dim italic]No open positions — execute a trade to get started[/dim italic]"
            )
            return

        lines = []
        for asset_id, pos in positions.items():
            price = self._prices.get(asset_id, 0.0)
            value = pos.market_value(price)
            pnl = pos.unrealized_pnl(price) if price > 0 else 0.0
            if price > 0:
                pnl_plain = f"+{_fmt_usd(pnl)}" if pnl > 0 else _fmt_usd(pnl)
                # Build entire line as plain text first for correct alignment
                plain = (
                    f"  {asset_id:<8} {pos.quantity:>10.4f} {_fmt_usd(pos.avg_cost):>10}"
                    f" {_fmt_usd(price):>10} {_fmt_usd(value):>12} {pnl_plain:>14}"
                )
                # Colorize just the P&L portion at the end
                pnl_start = plain.rfind(pnl_plain)
                if pnl > 0:
                    color = "green"
                elif pnl < 0:
                    color = "red"
                else:
                    color = "yellow"
                line = plain[:pnl_start] + f"[{color}]{pnl_plain}[/{color}]"
            else:
                line = (
                    f"  {asset_id:<8} {pos.quantity:>10.4f} {_fmt_usd(pos.avg_cost):>10}"
                    f" {'---':>10} {'---':>12} {'---':>14}"
                )
            lines.append(line)
        self.query_one("#tp-positions", Static).update("\n".join(lines))

    def _refresh_history(self) -> None:
        trades = self._portfolio.trades
        if not trades:
            self.query_one("#tp-history", Static).update(
                "  [dim italic]No trades yet[/dim italic]"
            )
            return

        # Show most recent trades first, limit to last 20
        lines = []
        for t in reversed(trades[-20:]):
            ts = t.timestamp[:19]  # trim to seconds
            side_text = t.side.upper()
            color = "green" if t.side == "buy" else "red"
            # Build plain line, then inject color around SIDE
            plain = (
                f"  {ts:<20} {side_text:<5} {t.asset_id:<8}"
                f" {t.quantity:>10.4f} {_fmt_usd(t.price):>10} {_fmt_usd(t.total):>12}"
            )
            side_start = plain.index(side_text, 22)  # after timestamp
            side_end = side_start + len(side_text)
            line = (
                plain[:side_start]
                + f"[{color}]{side_text}[/{color}]"
                + plain[side_end:]
            )
            lines.append(line)
        self.query_one("#tp-history", Static).update("\n".join(lines))

    def execute_buy(self) -> None:
        """Execute a buy trade from the form inputs."""
        self._execute_trade("buy")

    def execute_sell(self) -> None:
        """Execute a sell trade from the form inputs."""
        self._execute_trade("sell")

    def _execute_trade(self, side: str) -> None:
        feedback = self.query_one("#tp-feedback", Static)

        # Get asset — custom ticker takes priority over dropdown
        custom = self.query_one("#trade-custom", Input).value.strip().upper()
        select = self.query_one("#trade-asset", Select)
        if custom:
            asset_id = custom
        elif select.value is not Select.BLANK:
            asset_id = select.value
        else:
            feedback.update("  [red]Enter a ticker or select from watchlist[/red]")
            return

        # Get quantity
        qty_input = self.query_one("#trade-qty", Input)
        qty_text = qty_input.value.strip()
        if not qty_text:
            feedback.update("  [red]Enter a quantity[/red]")
            return
        try:
            quantity = float(qty_text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            feedback.update("  [red]Enter a valid positive number[/red]")
            return

        # Get current price
        price = self._prices.get(asset_id, 0.0)
        if price <= 0:
            feedback.update(
                f"  [red]No price available for {asset_id} — "
                f"add it to your watchlist (F5) so prices stream in[/red]"
            )
            return

        # Execute
        try:
            if side == "buy":
                trade = self._portfolio.execute_buy(asset_id, quantity, price)
            else:
                trade = self._portfolio.execute_sell(asset_id, quantity, price)
            save_portfolio(self._portfolio)
            feedback.update(
                f"  [green]{side.upper()} {quantity:.4f} {asset_id} @ {_fmt_usd(price)}"
                f" = {_fmt_usd(trade.total)}[/green]"
            )
            qty_input.value = ""
            self.query_one("#trade-custom", Input).value = ""
            self._refresh_all()
        except ValueError as e:
            feedback.update(f"  [red]{e}[/red]")

    def reset_portfolio(self) -> None:
        """Reset portfolio to initial state."""
        from ploomberg.paper_trading import Portfolio, DEFAULT_CASH, save_portfolio
        self._portfolio = Portfolio(cash=DEFAULT_CASH, initial_cash=DEFAULT_CASH, trades=[])
        save_portfolio(self._portfolio)
        self.query_one("#tp-feedback", Static).update(
            f"  [yellow]Portfolio reset to {_fmt_usd(DEFAULT_CASH)} cash[/yellow]"
        )
        self._refresh_all()

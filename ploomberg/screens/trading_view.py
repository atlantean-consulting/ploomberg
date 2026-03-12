"""F6 — Paper trading simulator view."""

from __future__ import annotations

from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.trading_panel import TradingPanel
from ploomberg.widgets.status_bar import StatusBar
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.messages import PriceUpdate
from ploomberg.paper_trading import load_portfolio


class TradingView(Screen):
    DEFAULT_CSS = """
    TradingView {
        layout: vertical;
    }
    """

    BINDINGS = [
        Binding("f9", "buy", "Buy", priority=True),
        Binding("f10", "sell", "Sell", priority=True),
        Binding("f12", "reset", "Reset", priority=True),
    ]

    def compose(self) -> ComposeResult:
        portfolio = load_portfolio()
        yield HeaderBar("P A P E R   T R A D I N G")
        yield TradingPanel(portfolio)
        yield StatusBar()
        yield CommandHints(
            "[bold]F9[/] Buy  [bold]F10[/] Sell  [bold]F12[/] Reset  "
            "[bold]F1[/] Dashboard  [bold]F3[/] Chart  "
            "[bold]F4[/] Stash  [bold]F5[/] Edit  [bold]Q[/] Quit"
        )

    def on_price_update(self, event: PriceUpdate) -> None:
        """Forward price data to the trading panel."""
        price_map = {
            asset_id: ap.price for asset_id, ap in event.prices.items()
        }
        self.query_one(TradingPanel).update_prices(price_map)

    def action_buy(self) -> None:
        self.query_one(TradingPanel).execute_buy()

    def action_sell(self) -> None:
        self.query_one(TradingPanel).execute_sell()

    def action_reset(self) -> None:
        self.query_one(TradingPanel).reset_portfolio()

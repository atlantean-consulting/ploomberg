"""Modal screen for adding a new asset to the watchlist."""

from __future__ import annotations

import asyncio

from textual.screen import ModalScreen
from textual.widgets import Static, Input
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical

from ploomberg.config import AVAILABLE_ASSETS, save_config, register_custom_assets


class AddAssetScreen(ModalScreen[bool]):
    DEFAULT_CSS = """
    AddAssetScreen {
        align: center middle;
    }
    AddAssetScreen #add-dialog {
        width: 60;
        height: auto;
        max-height: 12;
        border: heavy $accent;
        background: $background;
        padding: 1 2;
    }
    AddAssetScreen #add-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        height: 1;
        margin-bottom: 1;
    }
    AddAssetScreen #add-help {
        color: $text-muted;
        height: 1;
        margin-bottom: 1;
    }
    AddAssetScreen #add-error {
        color: $error;
        height: 1;
    }
    AddAssetScreen Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Static("Add Asset", id="add-title")
            yield Static("Format: EXCHANGE:SYMBOL (e.g. NYSE:T) or SYMBOL (e.g. AAPL)", id="add-help")
            yield Input(placeholder="NYSE:T", id="add-input")
            yield Static("", id="add-error")

    def on_mount(self) -> None:
        self.query_one("#add-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip().upper()
        if not raw:
            return

        error_label = self.query_one("#add-error", Static)

        # Parse EXCHANGE:SYMBOL or plain SYMBOL
        if ":" in raw:
            exchange, symbol = raw.split(":", 1)
        else:
            exchange, symbol = "", raw

        if not symbol:
            error_label.update("[red]Please enter a symbol[/red]")
            return

        # Check if already in watchlist
        asset_id = symbol.replace("=", "_").replace(".", "_")
        if asset_id in self.app.config.watchlist:
            error_label.update(f"[red]{asset_id} is already in your watchlist[/red]")
            return

        # Validate via yfinance in a thread
        error_label.update("[yellow]Looking up ticker...[/yellow]")
        self.refresh()

        try:
            result = await asyncio.to_thread(self._lookup_ticker, symbol)
        except Exception:
            result = None

        if result is None:
            error_label.update(f"[red]Could not find ticker: {symbol}[/red]")
            return

        ticker_name, yf_symbol = result

        # Register in config
        asset_info = {
            "name": ticker_name,
            "provider": "yahoo",
            "symbol": yf_symbol,
            "unit": "",
        }
        if exchange:
            asset_info["exchange"] = exchange

        self.app.config.custom_assets[asset_id] = asset_info
        self.app.config.watchlist.append(asset_id)
        register_custom_assets(self.app.config)
        save_config(self.app.config)

        self.dismiss(True)

    @staticmethod
    def _lookup_ticker(symbol: str) -> tuple[str, str] | None:
        """Validate a ticker symbol via yfinance. Returns (name, yf_symbol) or None."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.last_price
            if price is None or price == 0:
                return None
            # Try to get a readable name
            try:
                name = ticker.info.get("shortName") or ticker.info.get("longName") or symbol
            except Exception:
                name = symbol
            return (name, symbol)
        except Exception:
            return None

    def action_cancel(self) -> None:
        self.dismiss(False)

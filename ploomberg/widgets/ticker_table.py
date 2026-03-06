"""Main price ticker table widget."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult

from ploomberg.providers.base import AssetPrice
from ploomberg.config import AVAILABLE_ASSETS


class TickerTable(Container):
    DEFAULT_CSS = """
    TickerTable {
        height: 1fr;
        width: 100%;
        border: heavy $accent;
        padding: 0 1;
    }
    TickerTable .ticker-header {
        text-style: bold;
        color: $text-muted;
        height: 1;
    }
    TickerTable .ticker-separator {
        height: 1;
        color: $text-muted;
    }
    TickerTable .ticker-row {
        height: 1;
    }
    """

    def __init__(self, watchlist: list[str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._watchlist = watchlist or []
        self._prices: dict[str, AssetPrice] = {}

    def compose(self) -> ComposeResult:
        yield Static(
            "  ASSET          PRICE (USD)        24H CHG     ",
            classes="ticker-header",
        )
        yield Static("  " + "─" * 46, classes="ticker-separator")
        for asset_id in self._watchlist:
            info = AVAILABLE_ASSETS.get(asset_id, {})
            name = info.get("name", asset_id)
            yield Static(f"  ─ {name:<14} {'---':>14}     {'---':>8}", id=f"row-{asset_id}", classes="ticker-row")

    def update_prices(self, prices: dict[str, AssetPrice]) -> None:
        self._prices = prices
        for asset_id in self._watchlist:
            try:
                row = self.query_one(f"#row-{asset_id}", Static)
            except Exception:
                continue

            if asset_id in prices:
                p = prices[asset_id]
                # Direction indicator
                if p.change_pct > 0:
                    arrow = "[green]▲[/green]"
                    change_str = f"[green]+{p.change_pct:.2f}%[/green]"
                elif p.change_pct < 0:
                    arrow = "[red]▼[/red]"
                    change_str = f"[red]{p.change_pct:.2f}%[/red]"
                else:
                    arrow = "[yellow]─[/yellow]"
                    change_str = f"[yellow]{p.change_pct:.2f}%[/yellow]"

                # Format price
                if p.price >= 1000:
                    price_str = f"${p.price:,.2f}"
                elif p.price >= 1:
                    price_str = f"${p.price:.4f}"
                else:
                    price_str = f"${p.price:.6f}"

                row.update(
                    f"  {arrow} {p.name:<14} {price_str:>14}     {change_str:>8}"
                )
            else:
                info = AVAILABLE_ASSETS.get(asset_id, {})
                name = info.get("name", asset_id)
                row.update(f"  [yellow]─[/yellow] {name:<14} {'---':>14}     {'---':>8}")

    async def set_watchlist(self, watchlist: list[str]) -> None:
        self._watchlist = watchlist
        # Full re-render needed for watchlist changes
        await self.remove_children()
        await self.mount(
            Static(
                "  ASSET          PRICE (USD)        24H CHG     ",
                classes="ticker-header",
            )
        )
        await self.mount(Static("  " + "─" * 46, classes="ticker-separator"))
        for asset_id in watchlist:
            info = AVAILABLE_ASSETS.get(asset_id, {})
            name = info.get("name", asset_id)
            await self.mount(
                Static(
                    f"  ─ {name:<14} {'---':>14}     {'---':>8}",
                    id=f"row-{asset_id}",
                    classes="ticker-row",
                )
            )
        # Re-apply any existing prices
        if self._prices:
            self.update_prices(self._prices)

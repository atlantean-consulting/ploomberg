"""Main price ticker table widget."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult

from ploomberg.providers.base import AssetPrice
from ploomberg.config import AVAILABLE_ASSETS, SEPARATOR


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
        self._show_pct: bool = True

    def toggle_change_mode(self) -> None:
        """Toggle between percentage and dollar change display."""
        self._show_pct = not self._show_pct
        self._update_header()
        if self._prices:
            self.update_prices(self._prices)

    def _update_header(self) -> None:
        col_label = "24H CHG" if self._show_pct else "24H CHG $"
        try:
            header = self.query_one(".ticker-header", Static)
            header.update(f"  ASSET          PRICE (USD)        {col_label:<12}")
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Static(
            "  ASSET          PRICE (USD)        24H CHG     ",
            classes="ticker-header",
        )
        yield Static("  " + "─" * 46, classes="ticker-separator")
        sep_count = 0
        for asset_id in self._watchlist:
            if asset_id == SEPARATOR:
                yield Static("  " + "─" * 46, id=f"sep-{sep_count}", classes="ticker-separator")
                sep_count += 1
            else:
                info = AVAILABLE_ASSETS.get(asset_id, {})
                name = info.get("name", asset_id)
                yield Static(f"  ─ {name:<14} {'---':>14}     {'---':>8}", id=f"row-{asset_id}", classes="ticker-row")

    def update_prices(self, prices: dict[str, AssetPrice]) -> None:
        self._prices = prices
        for asset_id in self._watchlist:
            if asset_id == SEPARATOR:
                continue
            try:
                row = self.query_one(f"#row-{asset_id}", Static)
            except Exception:
                continue

            if asset_id in prices:
                p = prices[asset_id]

                # Direction indicator and color
                if p.change_pct > 0:
                    arrow = "[green]▲[/green]"
                    color = "green"
                elif p.change_pct < 0:
                    arrow = "[red]▼[/red]"
                    color = "red"
                else:
                    arrow = "[yellow]─[/yellow]"
                    color = "yellow"

                # Format change value
                if self._show_pct:
                    sign = "+" if p.change_pct > 0 else ""
                    change_plain = f"{sign}{p.change_pct:.2f}%"
                else:
                    # Compute dollar change from pct
                    if abs(p.change_pct) > 1e-9:
                        prev = p.price / (1 + p.change_pct / 100)
                        change_dollar = p.price - prev
                    else:
                        change_dollar = 0.0
                    sign = "+" if change_dollar > 0 else ""
                    change_plain = f"{sign}${change_dollar:,.2f}"

                # Format price
                if p.price >= 1000:
                    price_str = f"${p.price:,.2f}"
                elif p.price >= 1:
                    price_str = f"${p.price:.4f}"
                else:
                    price_str = f"${p.price:.6f}"

                # Build plain line then inject color markup
                rest = f" {p.name:<14} {price_str:>14}     {change_plain:>8}"
                chg_start = rest.rfind(change_plain)
                line = f"  {arrow}{rest[:chg_start]}[{color}]{change_plain}[/{color}]"
                row.update(line)
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
        sep_count = 0
        for asset_id in watchlist:
            if asset_id == SEPARATOR:
                await self.mount(
                    Static("  " + "─" * 46, id=f"sep-{sep_count}", classes="ticker-separator")
                )
                sep_count += 1
            else:
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

"""F4 — Silver stash tracker view."""

from __future__ import annotations

from textual.screen import Screen
from textual.app import ComposeResult

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.stash_table import StashTable
from ploomberg.widgets.status_bar import StatusBar
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.messages import PriceUpdate
from ploomberg.stash import load_stash


class StashView(Screen):
    DEFAULT_CSS = """
    StashView {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        stash = load_stash()
        yield HeaderBar("S I L V E R   S T A S H")
        yield StashTable(stash)
        yield StatusBar()
        yield CommandHints(
            "[bold]F1[/] Dashboard  [bold]F2[/] Convert  [bold]F3[/] Chart  "
            "[bold]F6[/] Trade  [bold]F5[/] Edit  [bold]F7[/] Theme  [bold]Q[/] Quit"
        )

    def on_price_update(self, event: PriceUpdate) -> None:
        """Forward silver spot price to the stash table."""
        xag = event.prices.get("XAG")
        if xag:
            self.query_one(StashTable).update_spot_price(xag.price)

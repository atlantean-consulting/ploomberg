"""Currency/commodity converter view."""

from __future__ import annotations

from textual.screen import Screen
from textual.app import ComposeResult

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.converter_form import ConverterForm
from ploomberg.widgets.status_bar import StatusBar
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.messages import PriceUpdate


class ConverterView(Screen):
    DEFAULT_CSS = """
    ConverterView {
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield HeaderBar("C O N V E R T E R")
        yield ConverterForm()
        yield StatusBar()
        yield CommandHints("[bold]F1[/] Dashboard  [bold]F5[/] Edit  [bold]F7[/] Theme  [bold]Q[/] Quit")

    def on_price_update(self, event: PriceUpdate) -> None:
        self.query_one(ConverterForm).update_prices(event.prices)

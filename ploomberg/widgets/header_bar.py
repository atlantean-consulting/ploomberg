"""Top branding bar for Ploomberg."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult


class HeaderBar(Container):
    DEFAULT_CSS = """
    HeaderBar {
        height: 3;
        width: 100%;
        content-align: center middle;
        border: heavy $accent;
    }
    HeaderBar #brand {
        width: 100%;
        text-align: center;
        text-style: bold;
    }
    HeaderBar .brand-warning {
        color: yellow;
    }
    """

    def __init__(self, title: str = "P L O O M B E R G", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._warning_timer = None

    def compose(self) -> ComposeResult:
        yield Static(self._title, id="brand", classes="header-text")

    def flash_warning(self, text: str, duration: float = 30.0) -> None:
        """Replace the brand text with a warning, revert after duration."""
        brand = self.query_one("#brand", Static)
        brand.update(f"[bold yellow]{text}[/bold yellow]")
        brand.remove_class("header-text")
        brand.add_class("brand-warning")
        if self._warning_timer is not None:
            self._warning_timer.stop()
        self._warning_timer = self.set_timer(duration, self._restore_brand)

    def _restore_brand(self) -> None:
        """Restore the original brand text."""
        brand = self.query_one("#brand", Static)
        brand.update(self._title)
        brand.remove_class("brand-warning")
        brand.add_class("header-text")
        self._warning_timer = None

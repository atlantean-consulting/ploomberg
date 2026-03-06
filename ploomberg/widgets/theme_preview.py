"""Live theme preview panel for the theme editor."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult

from ploomberg.themes import Theme


class ThemePreview(Container):
    DEFAULT_CSS = """
    ThemePreview {
        height: auto;
        width: 100%;
        border: round $accent;
        padding: 1 2;
        margin-top: 1;
    }
    ThemePreview .preview-title {
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    ThemePreview .preview-row {
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Preview", classes="preview-title")
        yield Static("", id="preview-row-1", classes="preview-row")
        yield Static("", id="preview-row-2", classes="preview-row")
        yield Static("", id="preview-row-3", classes="preview-row")

    def update_preview(self, theme: Theme) -> None:
        r1 = self.query_one("#preview-row-1", Static)
        r2 = self.query_one("#preview-row-2", Static)
        r3 = self.query_one("#preview-row-3", Static)

        r1.update(f"[{theme.price_up}]▲ Gold       $2,847.30   +1.23%[/]")
        r2.update(f"[{theme.price_down}]▼ Silver     $31.45      -0.87%[/]")
        r3.update(f"[{theme.price_flat}]─ Copper     $4.12       +0.00%[/]")

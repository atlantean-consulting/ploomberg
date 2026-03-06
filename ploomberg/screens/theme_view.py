"""Theme editor view for selecting and previewing themes."""

from __future__ import annotations

from textual.screen import Screen
from textual.widgets import Static, ListView, ListItem, Label
from textual.app import ComposeResult
from textual.binding import Binding

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.theme_preview import ThemePreview
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.themes import BUILTIN_THEMES
from ploomberg.config import save_config


class ThemeView(Screen):
    DEFAULT_CSS = """
    ThemeView {
        layout: vertical;
    }
    ThemeView .theme-section-label {
        height: 1;
        margin: 1 1 0 1;
        text-style: bold;
    }
    ThemeView ListView {
        height: auto;
        max-height: 10;
        border: heavy $accent;
        margin: 0 1;
    }
    ThemeView ThemePreview {
        margin: 0 1;
    }
    ThemeView .active-theme {
        color: $success;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("enter", "apply_theme", "Apply", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield HeaderBar("T H E M E   E D I T O R")
        yield Static("Built-in Themes:", classes="theme-section-label")
        yield ListView(*self._build_items())
        yield ThemePreview()
        yield CommandHints("[bold]Enter[/] Apply  [bold]F1[/] Dashboard  [bold]F5[/] Edit  [bold]Q[/] Quit")

    def _build_items(self) -> list[ListItem]:
        current = self.app.config.theme
        items = []
        for theme_id, theme in BUILTIN_THEMES.items():
            marker = "[green]●[/green]" if theme_id == current else "○"
            label = Label(f" {marker} {theme.name}")
            item = ListItem(label, id=f"theme-{theme_id}")
            if theme_id == current:
                item.add_class("active-theme")
            items.append(item)
        return items

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update preview when cursor moves."""
        if event.item is None:
            return
        theme_id = event.item.id
        if theme_id and theme_id.startswith("theme-"):
            tid = theme_id[6:]
            if tid in BUILTIN_THEMES:
                self.query_one(ThemePreview).update_preview(BUILTIN_THEMES[tid])

    async def action_apply_theme(self) -> None:
        list_view = self.query_one(ListView)
        idx = list_view.index
        if idx is None:
            return

        theme_ids = list(BUILTIN_THEMES.keys())
        if idx >= len(theme_ids):
            return

        theme_id = theme_ids[idx]
        self.app.config.theme = theme_id
        save_config(self.app.config)

        # Apply theme CSS
        self.app.apply_theme(theme_id)

        # Refresh markers
        await self._refresh_list()

    async def _refresh_list(self) -> None:
        list_view = self.query_one(ListView)
        idx = list_view.index
        await list_view.clear()
        for item in self._build_items():
            await list_view.append(item)
        if idx is not None:
            list_view.index = idx

    def on_mount(self) -> None:
        """Show preview for current theme on mount."""
        current = self.app.config.theme
        if current in BUILTIN_THEMES:
            self.query_one(ThemePreview).update_preview(BUILTIN_THEMES[current])

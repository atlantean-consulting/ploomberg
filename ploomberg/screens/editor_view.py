"""Dashboard editor view for managing watched assets."""

from __future__ import annotations

from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label
from textual.app import ComposeResult
from textual.binding import Binding

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.config import AVAILABLE_ASSETS, SEPARATOR, save_config


class EditorView(Screen):
    DEFAULT_CSS = """
    EditorView {
        layout: vertical;
    }
    EditorView ListView {
        height: 1fr;
        border: heavy $accent;
        padding: 0 1;
    }
    EditorView .hidden-item {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("pageup", "move_up", "Move Up", priority=True),
        Binding("pagedown", "move_down", "Move Down", priority=True),
        Binding("h", "toggle_hidden", "Hide", priority=True),
        Binding("d", "delete_asset", "Delete", priority=True),
        Binding("a", "add_asset", "Add", priority=True),
        Binding("s", "add_separator", "Separator", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield HeaderBar("D A S H B O A R D   E D I T O R")
        yield ListView(*self._build_items())
        yield CommandHints(
            "[bold]PgUp/PgDn[/] Reorder  [bold]H[/] Hide  "
            "[bold]D[/] Delete  [bold]A[/] Add  [bold]S[/] Separator  "
            "[bold]F1[/] Dashboard  [bold]Q[/] Quit"
        )

    def _build_items(self) -> list[ListItem]:
        watchlist = self.app.config.watchlist
        hidden = self.app.config.hidden_assets
        items = []
        sep_count = 0
        for asset_id in watchlist:
            if asset_id == SEPARATOR:
                label = Label(" [dim]──────────── separator ────────────[/dim]")
                items.append(ListItem(label, id=f"editor-sep-{sep_count}"))
                sep_count += 1
            else:
                info = AVAILABLE_ASSETS.get(asset_id, {})
                name = info.get("name", asset_id)
                exchange = info.get("exchange", "")
                exchange_tag = f" [{exchange}]" if exchange else ""
                is_hidden = asset_id in hidden
                if is_hidden:
                    text = f" [dim]▸ {name} ({asset_id}){exchange_tag} (hidden)[/dim]"
                else:
                    text = f" ▸ {name} ({asset_id}){exchange_tag}"
                label = Label(text)
                item = ListItem(label, id=f"editor-{asset_id}")
                if is_hidden:
                    item.add_class("hidden-item")
                items.append(item)
        return items

    def _get_selected_index(self) -> int | None:
        list_view = self.query_one(ListView)
        idx = list_view.index
        if idx is None:
            return None
        watchlist = self.app.config.watchlist
        if idx >= len(watchlist):
            return None
        return idx

    async def action_move_up(self) -> None:
        idx = self._get_selected_index()
        if idx is None or idx == 0:
            return
        watchlist = self.app.config.watchlist
        watchlist[idx - 1], watchlist[idx] = watchlist[idx], watchlist[idx - 1]
        save_config(self.app.config)
        await self._refresh_list()
        self.query_one(ListView).index = idx - 1

    async def action_move_down(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        watchlist = self.app.config.watchlist
        if idx >= len(watchlist) - 1:
            return
        watchlist[idx], watchlist[idx + 1] = watchlist[idx + 1], watchlist[idx]
        save_config(self.app.config)
        await self._refresh_list()
        self.query_one(ListView).index = idx + 1

    async def action_toggle_hidden(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        asset_id = self.app.config.watchlist[idx]
        if asset_id == SEPARATOR:
            return
        hidden = self.app.config.hidden_assets
        if asset_id in hidden:
            hidden.remove(asset_id)
        else:
            hidden.append(asset_id)
        save_config(self.app.config)
        await self._refresh_list()

    async def action_delete_asset(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        asset_id = self.app.config.watchlist[idx]
        self.app.config.watchlist.remove(asset_id)
        if asset_id in self.app.config.hidden_assets:
            self.app.config.hidden_assets.remove(asset_id)
        save_config(self.app.config)
        await self._refresh_list()

    async def action_add_separator(self) -> None:
        """Insert a separator line below the current selection."""
        idx = self._get_selected_index()
        insert_at = (idx + 1) if idx is not None else len(self.app.config.watchlist)
        self.app.config.watchlist.insert(insert_at, SEPARATOR)
        save_config(self.app.config)
        await self._refresh_list()
        self.query_one(ListView).index = insert_at

    def action_add_asset(self) -> None:
        from ploomberg.screens.add_asset_screen import AddAssetScreen

        self.app.push_screen(AddAssetScreen(), callback=self._on_add_result)

    async def _on_add_result(self, result: bool) -> None:
        if result:
            await self._refresh_list()

    async def _refresh_list(self) -> None:
        list_view = self.query_one(ListView)
        idx = list_view.index
        await list_view.clear()
        for item in self._build_items():
            await list_view.append(item)
        if idx is not None and idx < len(self.app.config.watchlist):
            list_view.index = idx

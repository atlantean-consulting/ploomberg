"""Custom Textual messages for inter-widget communication."""

from __future__ import annotations

from textual.message import Message


class PriceUpdate(Message):
    """Broadcast updated prices to all widgets."""

    def __init__(self, prices: dict) -> None:
        super().__init__()
        self.prices = prices


class AssetAdded(Message):
    """User added an asset to the watchlist."""

    def __init__(self, asset_id: str) -> None:
        super().__init__()
        self.asset_id = asset_id


class AssetRemoved(Message):
    """User removed an asset from the watchlist."""

    def __init__(self, asset_id: str) -> None:
        super().__init__()
        self.asset_id = asset_id


class ThemeChanged(Message):
    """User selected a new theme."""

    def __init__(self, theme_id: str) -> None:
        super().__init__()
        self.theme_id = theme_id

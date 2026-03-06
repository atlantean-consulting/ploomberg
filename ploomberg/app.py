"""Ploomberg main application."""

from __future__ import annotations

import asyncio
from datetime import datetime

from textual.app import App
from textual.binding import Binding

from ploomberg.config import (
    PloombergConfig,
    load_config,
    register_custom_assets,
    AVAILABLE_ASSETS,
)
from ploomberg.messages import PriceUpdate
from ploomberg.providers.base import AssetPrice
from ploomberg.providers.frankfurter import FrankfurterProvider
from ploomberg.providers.coingecko import CoinGeckoProvider
from ploomberg.providers.metals import MetalsProvider
from ploomberg.providers.yahoo import YahooProvider
from ploomberg.screens.dashboard_view import DashboardView
from ploomberg.screens.converter_view import ConverterView
from ploomberg.screens.chart_view import ChartView
from ploomberg.screens.editor_view import EditorView
from ploomberg.screens.theme_view import ThemeView
from ploomberg.themes import BUILTIN_THEMES, DEFAULT_THEME, Theme


class PloombergApp(App):
    TITLE = "ploomberg"

    MODES = {
        "dashboard": DashboardView,
        "converter": ConverterView,
        "chart": ChartView,
        "editor": EditorView,
        "theme": ThemeView,
    }

    DEFAULT_MODE = "dashboard"

    BINDINGS = [
        Binding("f1", "switch_dashboard", "Dashboard", priority=True),
        Binding("f2", "switch_converter", "Converter", priority=True),
        Binding("f3", "switch_chart", "Chart", priority=True),
        Binding("f5", "switch_editor", "Editor", priority=True),
        Binding("f7", "switch_theme", "Theme", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    CSS = """
    Screen {
        background: $background;
        color: $text;
    }
    Footer {
        background: $surface;
    }
    .price-up {
        color: $success;
    }
    .price-down {
        color: $error;
    }
    .price-flat {
        color: $warning;
    }
    .header-text {
        color: $primary;
        text-style: bold;
    }
    .accent {
        color: $accent;
    }
    """

    def __init__(self) -> None:
        self.config: PloombergConfig = load_config()
        register_custom_assets(self.config)
        self._theme = BUILTIN_THEMES.get(self.config.theme, BUILTIN_THEMES[DEFAULT_THEME])
        super().__init__()
        self.prices: dict[str, AssetPrice] = {}
        self._last_update: datetime | None = None
        self._online = False
        self._countdown = 0

        # Initialize providers
        self._providers = [
            FrankfurterProvider(),
            CoinGeckoProvider(),
            MetalsProvider(),
            YahooProvider(),
        ]

    def get_css_variables(self) -> dict[str, str]:
        """Override to inject theme colors as CSS variables."""
        variables = super().get_css_variables()
        t = self._theme
        variables["background"] = t.background
        variables["surface"] = t.border
        variables["text"] = t.foreground
        variables["primary"] = t.header
        variables["secondary"] = t.border
        variables["accent"] = t.accent
        variables["success"] = t.price_up
        variables["error"] = t.price_down
        variables["warning"] = t.price_flat
        return variables

    def apply_theme(self, theme_id: str) -> None:
        """Apply a theme dynamically."""
        self._theme = BUILTIN_THEMES.get(theme_id, BUILTIN_THEMES[DEFAULT_THEME])
        if self.is_running:
            self.refresh_css()

    def on_mount(self) -> None:
        self._countdown = self.config.refresh_interval
        self.set_interval(1, self._tick)
        # Fetch immediately on start
        self.call_later(self._poll_prices)

    def _tick(self) -> None:
        """Called every second to update countdown and trigger fetches."""
        self._countdown -= 1
        if self._countdown <= 0:
            self._countdown = self.config.refresh_interval
            self.call_later(self._poll_prices)

        # Update status bar on current screen
        self._update_status_bars()

    def _update_status_bars(self) -> None:
        """Update all StatusBar widgets on the current screen."""
        from ploomberg.widgets.status_bar import StatusBar

        if self.screen:
            for widget in self.screen.walk_children():
                if isinstance(widget, StatusBar):
                    widget.update_status(self._online, self._last_update, self._countdown)

    async def _poll_prices(self) -> None:
        """Fetch prices from all providers concurrently."""
        watchlist = self.config.watchlist

        # Group symbols by provider
        provider_symbols: dict[str, list[str]] = {}
        for asset_id in watchlist:
            info = AVAILABLE_ASSETS.get(asset_id)
            if info:
                provider = info["provider"]
                provider_symbols.setdefault(provider, []).append(asset_id)

        # Map provider names to instances
        provider_map = {
            "frankfurter": self._providers[0],
            "coingecko": self._providers[1],
            "metals": self._providers[2],
            "yahoo": self._providers[3],
        }

        # Fetch from all needed providers concurrently
        tasks = []
        for provider_name, symbols in provider_symbols.items():
            provider = provider_map.get(provider_name)
            if provider:
                tasks.append(provider.fetch_prices(symbols))

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            new_prices: dict[str, AssetPrice] = {}
            any_success = False

            for result in results:
                if isinstance(result, dict):
                    new_prices.update(result)
                    if result:
                        any_success = True

            if new_prices:
                self.prices.update(new_prices)
                self._last_update = datetime.now()

            self._online = any_success

        except Exception:
            self._online = False

        # Broadcast to current screen's widgets
        self._broadcast_prices()

    def _broadcast_prices(self) -> None:
        """Send PriceUpdate to the current screen."""
        if self.screen and self.prices:
            self.screen.post_message(PriceUpdate(dict(self.prices)))

    # Mode switching actions
    def action_switch_dashboard(self) -> None:
        self.switch_mode("dashboard")
        self.call_later(self._broadcast_prices)

    def action_switch_converter(self) -> None:
        self.switch_mode("converter")
        self.call_later(self._broadcast_prices)

    def action_switch_chart(self) -> None:
        self.switch_mode("chart")

    def action_switch_editor(self) -> None:
        self.switch_mode("editor")

    def action_switch_theme(self) -> None:
        self.switch_mode("theme")

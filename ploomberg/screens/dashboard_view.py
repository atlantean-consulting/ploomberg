"""Main dashboard ticker view."""

from __future__ import annotations

import time

from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container

from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.ticker_table import TickerTable
from ploomberg.widgets.status_bar import StatusBar
from ploomberg.widgets.command_hints import CommandHints
from ploomberg.messages import PriceUpdate

# Rate limit window in seconds
_RATE_WINDOW = 30.0


class TiltOverlay(Container):
    DEFAULT_CSS = """
    TiltOverlay {
        display: none;
        layer: tilt;
        width: 100%;
        height: 100%;
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    TiltOverlay #tilt-box {
        width: 62;
        height: auto;
        border: heavy red;
        background: $background;
        padding: 1 2;
    }
    TiltOverlay #tilt-art {
        width: 100%;
        text-align: center;
        color: orange;
    }
    TiltOverlay #tilt-text {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: red;
        margin-top: 1;
    }
    """

    BANK_FIRE = r"""
        )  )   )        )  )   )
       (  (  (         (  (  (
        )  )   )        )  )   )
      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     {  $   $   $   BANK   $   $   $  }
     {      _________________________  }
     {     |  ####  || |  ####  |    | }
     {     |  ####  || |  ####  |    | }
     {     |  ####  || |  ####  |    | }
     {     |________||_|________|____| }
      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    def compose(self) -> ComposeResult:
        with Container(id="tilt-box"):
            yield Static(self.BANK_FIRE, id="tilt-art")
            yield Static("", id="tilt-text")

    def show_tilt(self, remaining: int) -> None:
        self.query_one("#tilt-text", Static).update(
            f"TILT - TILT - TERMINAL LOCKOUT {remaining}s - TILT - TILT"
        )
        self.styles.display = "block"

    def hide_tilt(self) -> None:
        self.styles.display = "none"


class DashboardView(Screen):
    DEFAULT_CSS = """
    DashboardView {
        layout: vertical;
        layers: default tilt;
    }
    """

    BINDINGS = [
        Binding("r", "force_refresh", "Refresh", priority=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._refresh_timestamps: list[float] = []
        self._tilt_until: float = 0.0
        self._tilt_timer = None

    def _visible_watchlist(self) -> list[str]:
        hidden = set(self.app.config.hidden_assets)
        return [a for a in self.app.config.watchlist if a not in hidden]

    def compose(self) -> ComposeResult:
        yield HeaderBar("P L O O M B E R G  v0.1")
        yield TickerTable(watchlist=self._visible_watchlist())
        yield TiltOverlay()
        yield StatusBar()
        yield CommandHints(
            "[bold]R[/] Refresh  [bold]F2[/] Convert  "
            "[bold]F5[/] Edit  [bold]F7[/] Theme  [bold]Q[/] Quit"
        )

    def action_force_refresh(self) -> None:
        now = time.monotonic()

        # If tilted, ignore input
        if now < self._tilt_until:
            return

        # Prune old timestamps outside the rate window
        self._refresh_timestamps = [
            t for t in self._refresh_timestamps if now - t < _RATE_WINDOW
        ]

        count = len(self._refresh_timestamps)

        if count == 0:
            # First refresh — clean, just do it
            self._refresh_timestamps.append(now)
            self.app._countdown = 0  # triggers fetch on next tick

        elif count == 1:
            # Second refresh within window — allow but flash warning
            self._refresh_timestamps.append(now)
            self.app._countdown = 0
            self.query_one(HeaderBar).flash_warning(
                " C A R E F U L ! ! ! ", duration=_RATE_WINDOW
            )

        else:
            # Third+ refresh within window — TILT
            self._tilt_until = now + _RATE_WINDOW
            self._refresh_timestamps.clear()
            self._start_tilt_countdown()

    def _start_tilt_countdown(self) -> None:
        overlay = self.query_one(TiltOverlay)
        remaining = max(0, int(self._tilt_until - time.monotonic()))
        overlay.show_tilt(remaining)
        if self._tilt_timer is not None:
            self._tilt_timer.stop()
        self._tilt_timer = self.set_interval(1, self._tick_tilt)

    def _tick_tilt(self) -> None:
        remaining = max(0, int(self._tilt_until - time.monotonic()))
        overlay = self.query_one(TiltOverlay)
        if remaining <= 0:
            overlay.hide_tilt()
            if self._tilt_timer is not None:
                self._tilt_timer.stop()
                self._tilt_timer = None
        else:
            overlay.show_tilt(remaining)

    async def on_price_update(self, event: PriceUpdate) -> None:
        table = self.query_one(TickerTable)
        visible = self._visible_watchlist()
        if table._watchlist != visible:
            await table.set_watchlist(visible)
        table.update_prices(event.prices)

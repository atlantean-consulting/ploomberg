"""Bottom status bar showing time, data freshness, market status, and connection."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from textual.containers import Container
from textual.widgets import Static
from textual.app import ComposeResult


# Market schedule: (tz_name, open_hour, open_min, close_hour, close_min)
MARKETS = {
    "NY": ("America/New_York", 9, 30, 16, 0),
    "GB": ("Europe/London", 8, 0, 16, 30),
    "JP": ("Asia/Tokyo", 9, 0, 15, 0),  # simplified (ignores lunch break)
}


def _market_status(label: str, tz_name: str, oh: int, om: int, ch: int, cm: int, now_utc: datetime) -> str:
    """Return a Rich-markup colored market label: green=open, yellow=closing soon, red=closed."""
    tz = ZoneInfo(tz_name)
    local = now_utc.astimezone(tz)

    # Closed on weekends
    if local.weekday() >= 5:
        return f"[red]{label}[/red]"

    open_mins = oh * 60 + om
    close_mins = ch * 60 + cm
    now_mins = local.hour * 60 + local.minute

    if now_mins < open_mins or now_mins >= close_mins:
        return f"[red]{label}[/red]"

    # Within 60 minutes of close
    if close_mins - now_mins <= 60:
        return f"[yellow]{label}[/yellow]"

    return f"[green]{label}[/green]"


class StatusBar(Container):
    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        width: 100%;
        border: heavy $accent;
        content-align: center middle;
    }
    StatusBar #status-text {
        width: 100%;
        text-align: center;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._last_update: datetime | None = None
        self._online = False
        self._countdown = 0

    def compose(self) -> ComposeResult:
        yield Static("Connecting...", id="status-text")

    def update_status(self, online: bool, last_update: datetime | None, countdown: int) -> None:
        self._online = online
        self._last_update = last_update
        self._countdown = countdown

        now_utc = datetime.now(timezone.utc)
        status_widget = self.query_one("#status-text", Static)

        # Current time with timezone
        local_now = datetime.now().astimezone()
        clock = local_now.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Data freshness
        if last_update:
            data_str = f"Data: {last_update.strftime('%H:%M:%S')}"
        else:
            data_str = "Data: --:--:--"

        # Countdown (zero-padded)
        next_str = f"Next: {countdown:02d}s"

        # Market indicators
        markets = " ".join(
            _market_status(label, *params, now_utc)
            for label, params in MARKETS.items()
        )

        # Online indicator (dot only)
        dot = "[green]●[/green]" if online else "[red]●[/red]"

        status_widget.update(f"{clock} │ {data_str} │ {next_str} │ {markets} │ {dot}")

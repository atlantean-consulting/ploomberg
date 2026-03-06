"""F3 — Historical price chart view."""

from __future__ import annotations

from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal

from ploomberg.config import AVAILABLE_ASSETS
from ploomberg.providers.history import PERIODS, HistoryData, fetch_history
from ploomberg.widgets.header_bar import HeaderBar
from ploomberg.widgets.price_chart import PriceChart
from ploomberg.widgets.status_bar import StatusBar
from ploomberg.widgets.command_hints import CommandHints


def _fmt_vol(vol: float) -> str:
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:,.1f}M"
    if vol >= 1_000:
        return f"{vol / 1_000:,.1f}K"
    return f"{vol:,.0f}"


class DetailPanel(Static):
    DEFAULT_CSS = """
    DetailPanel {
        width: 32;
        height: 1fr;
        padding: 1 2;
        border-left: tall $surface;
    }
    """

    def show_period_summary(self, asset_id: str, period_label: str, history: HistoryData | None) -> None:
        """Show summary stats for the entire period."""
        info = AVAILABLE_ASSETS.get(asset_id, {})
        name = info.get("name", asset_id)
        unit = info.get("unit", "")
        unit_str = f" / {unit}" if unit else ""

        if not history or not history.closes:
            self.update(f"[bold]{name}[/]\n\nNo data available")
            return

        closes = history.closes
        high = max(history.highs)
        low = min(history.lows)
        first, last = closes[0], closes[-1]
        change = last - first
        change_pct = (change / first * 100) if first != 0 else 0.0
        total_vol = sum(history.volumes)
        arrow, chg_color = _change_style(change)

        lines = [
            f"[bold]{name}[/]  ({asset_id})",
            f"Period: {period_label}",
            "",
            f"[bold]Last[/]     {last:>12,.2f}{unit_str}",
            f"[bold]Open[/]     {first:>12,.2f}",
            f"[bold]High[/]     {high:>12,.2f}",
            f"[bold]Low[/]      {low:>12,.2f}",
            "",
            f"[bold]Change[/]   {arrow} [{chg_color}]{change:>+,.2f}[/]",
            f"[bold]% Chg[/]    [{chg_color}]{change_pct:>+.2f}%[/]",
        ]

        if total_vol > 0:
            lines.extend(["", f"[bold]Volume[/]   {_fmt_vol(total_vol):>12}"])

        lines.extend(["", "", f"[dim]{len(closes)} data points[/]"])
        self.update("\n".join(lines))

    def show_cursor_point(self, asset_id: str, history: HistoryData, idx: int) -> None:
        """Show data for a single point under the cursor."""
        info = AVAILABLE_ASSETS.get(asset_id, {})
        name = info.get("name", asset_id)
        unit = info.get("unit", "")
        unit_str = f" / {unit}" if unit else ""

        dt = history.dates[idx]
        close = history.closes[idx]
        high = history.highs[idx]
        low = history.lows[idx]
        vol = history.volumes[idx]

        # Change from previous point
        if idx > 0:
            prev = history.closes[idx - 1]
            change = close - prev
            change_pct = (change / prev * 100) if prev != 0 else 0.0
        else:
            change = 0.0
            change_pct = 0.0

        arrow, chg_color = _change_style(change)

        # Date format depends on granularity
        n = len(history.dates)
        if n < 100 and (history.dates[-1] - history.dates[0]).days < 2:
            date_str = dt.strftime("%H:%M:%S")
        else:
            date_str = dt.strftime("%Y-%m-%d")

        lines = [
            f"[bold]{name}[/]  ({asset_id})",
            f"[bold reverse] {date_str} [/]",
            "",
            f"[bold]Price[/]    {close:>12,.2f}{unit_str}",
            f"[bold]High[/]     {high:>12,.2f}",
            f"[bold]Low[/]      {low:>12,.2f}",
            "",
            f"[bold]Change[/]   {arrow} [{chg_color}]{change:>+,.2f}[/]",
            f"[bold]% Chg[/]    [{chg_color}]{change_pct:>+.2f}%[/]",
        ]

        if vol > 0:
            lines.extend(["", f"[bold]Volume[/]   {_fmt_vol(vol):>12}"])

        lines.extend(["", "", f"[dim]Point {idx + 1} of {n}[/]"])
        self.update("\n".join(lines))


def _change_style(change: float) -> tuple[str, str]:
    if change > 0:
        return "[green]\u25b2[/]", "green"
    elif change < 0:
        return "[red]\u25bc[/]", "red"
    return "[yellow]\u2500[/]", "yellow"


class PeriodBar(Static):
    DEFAULT_CSS = """
    PeriodBar {
        height: 1;
        width: 100%;
        text-align: center;
        background: $surface;
    }
    """

    def render_bar(self, period_idx: int) -> None:
        parts = []
        for i, (label, _, _) in enumerate(PERIODS):
            key = str(i + 1)
            if i == period_idx:
                parts.append(f"[bold reverse] {key}:{label} [/]")
            else:
                parts.append(f" [bold]{key}[/]:{label} ")
        self.update("  ".join(parts))


class ChartView(Screen):
    DEFAULT_CSS = """
    ChartView {
        layout: vertical;
    }
    #chart-body {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("up", "prev_asset", "Prev asset", priority=True),
        Binding("down", "next_asset", "Next asset", priority=True),
        Binding("left", "cursor_left", "Cursor left", priority=True),
        Binding("right", "cursor_right", "Cursor right", priority=True),
        Binding("home", "cursor_home", "Cursor home", priority=True),
        Binding("end", "cursor_end", "Cursor end", priority=True),
        Binding("pageup", "cursor_pgup", "Page up", priority=True),
        Binding("pagedown", "cursor_pgdn", "Page down", priority=True),
        Binding("escape", "cursor_clear", "Clear cursor", priority=True),
        Binding("1", "period_1", "1D", priority=True),
        Binding("2", "period_2", "5D", priority=True),
        Binding("3", "period_3", "1M", priority=True),
        Binding("4", "period_4", "3M", priority=True),
        Binding("5", "period_5", "6M", priority=True),
        Binding("6", "period_6", "1Y", priority=True),
        Binding("plus,equal", "next_period", "+", priority=True, show=False),
        Binding("minus,underscore", "prev_period", "-", priority=True, show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._period_idx = 2  # default 1M
        self._asset_idx = 0
        self._cursor: int | None = None
        self._history: HistoryData | None = None
        self._loading = False

    def _watchlist(self) -> list[str]:
        hidden = set(self.app.config.hidden_assets)
        return [a for a in self.app.config.watchlist if a not in hidden]

    def _current_asset(self) -> str:
        wl = self._watchlist()
        if not wl:
            return ""
        self._asset_idx = self._asset_idx % len(wl)
        return wl[self._asset_idx]

    def compose(self) -> ComposeResult:
        yield HeaderBar("P L O O M B E R G  v0.1")
        yield PeriodBar()
        with Horizontal(id="chart-body"):
            yield PriceChart(id="chart")
            yield DetailPanel()
        yield StatusBar()
        yield CommandHints(
            "[bold]\u2190\u2192[/] Cursor  [bold]\u2191\u2193[/] Asset  "
            "[bold]+/-[/] Period  [bold]1-6[/] Period  "
            "[bold]Esc[/] Clear  [bold]Q[/] Quit"
        )

    def on_mount(self) -> None:
        self._sync_colors()
        self._load_chart()

    def _sync_colors(self) -> None:
        theme = self.app._theme
        self.query_one(PriceChart).set_colors({
            "background": theme.background,
            "foreground": theme.foreground,
            "accent": theme.accent,
        })

    def _load_chart(self) -> None:
        if self._loading:
            return
        asset_id = self._current_asset()
        if not asset_id:
            self.query_one(PriceChart).show_empty("No assets in watchlist")
            self.query_one(DetailPanel).update("No assets")
            return

        self._loading = True
        self._cursor = None
        self._history = None
        period_label = PERIODS[self._period_idx][0]
        name = AVAILABLE_ASSETS.get(asset_id, {}).get("name", asset_id)

        chart = self.query_one(PriceChart)
        chart.show_empty(f"Loading {name} ({period_label})...")
        self.query_one(PeriodBar).render_bar(self._period_idx)

        self.run_worker(self._fetch_and_render(asset_id, self._period_idx), exclusive=True)

    async def _fetch_and_render(self, asset_id: str, period_idx: int) -> None:
        try:
            history = await fetch_history(asset_id, period_idx)
        except Exception:
            history = None
        finally:
            self._loading = False

        self._history = history
        chart = self.query_one(PriceChart)
        detail = self.query_one(DetailPanel)
        period_label = PERIODS[period_idx][0]
        name = AVAILABLE_ASSETS.get(asset_id, {}).get("name", asset_id)

        if history and history.closes:
            chart.update_chart(history, f"{name} \u2014 {period_label}")
        else:
            chart.show_empty(f"{name} \u2014 no data for {period_label}")

        detail.show_period_summary(asset_id, period_label, history)

    def _update_detail_for_cursor(self) -> None:
        """Update detail panel based on cursor state."""
        detail = self.query_one(DetailPanel)
        asset_id = self._current_asset()
        if self._cursor is not None and self._history and self._history.closes:
            detail.show_cursor_point(asset_id, self._history, self._cursor)
        else:
            period_label = PERIODS[self._period_idx][0]
            detail.show_period_summary(asset_id, period_label, self._history)

    # Cursor actions
    def action_cursor_right(self) -> None:
        if not self._history or not self._history.closes:
            return
        n = len(self._history.closes)
        if self._cursor is None:
            self._cursor = 0
        else:
            self._cursor = min(self._cursor + 1, n - 1)
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_left(self) -> None:
        if not self._history or not self._history.closes:
            return
        n = len(self._history.closes)
        if self._cursor is None:
            self._cursor = n - 1
        else:
            self._cursor = max(self._cursor - 1, 0)
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_pgdn(self) -> None:
        if not self._history or not self._history.closes:
            return
        n = len(self._history.closes)
        step = max(1, n // 10)
        if self._cursor is None:
            self._cursor = step - 1
        else:
            self._cursor = min(self._cursor + step, n - 1)
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_pgup(self) -> None:
        if not self._history or not self._history.closes:
            return
        n = len(self._history.closes)
        step = max(1, n // 10)
        if self._cursor is None:
            self._cursor = n - step
        else:
            self._cursor = max(self._cursor - step, 0)
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_home(self) -> None:
        if not self._history or not self._history.closes:
            return
        self._cursor = 0
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_end(self) -> None:
        if not self._history or not self._history.closes:
            return
        self._cursor = len(self._history.closes) - 1
        self.query_one(PriceChart).set_cursor(self._cursor)
        self._update_detail_for_cursor()

    def action_cursor_clear(self) -> None:
        self._cursor = None
        self.query_one(PriceChart).set_cursor(None)
        self._update_detail_for_cursor()

    # Period actions
    def action_period_1(self) -> None:
        self._set_period(0)

    def action_period_2(self) -> None:
        self._set_period(1)

    def action_period_3(self) -> None:
        self._set_period(2)

    def action_period_4(self) -> None:
        self._set_period(3)

    def action_period_5(self) -> None:
        self._set_period(4)

    def action_period_6(self) -> None:
        self._set_period(5)

    def action_next_period(self) -> None:
        self._set_period(min(self._period_idx + 1, len(PERIODS) - 1))

    def action_prev_period(self) -> None:
        self._set_period(max(self._period_idx - 1, 0))

    def _set_period(self, idx: int) -> None:
        if idx != self._period_idx:
            self._period_idx = idx
            self.query_one(PeriodBar).render_bar(self._period_idx)
            self._load_chart()

    # Asset cycling
    def action_next_asset(self) -> None:
        wl = self._watchlist()
        if wl:
            self._asset_idx = (self._asset_idx + 1) % len(wl)
            self._load_chart()

    def action_prev_asset(self) -> None:
        wl = self._watchlist()
        if wl:
            self._asset_idx = (self._asset_idx - 1) % len(wl)
            self._load_chart()

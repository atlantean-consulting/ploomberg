"""Price chart widget wrapping textual-plotext."""

from __future__ import annotations

from textual_plotext import PlotextPlot

from ploomberg.providers.history import HistoryData


class PriceChart(PlotextPlot):
    DEFAULT_CSS = """
    PriceChart {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history: HistoryData | None = None
        self._title: str = ""
        self._colors: dict[str, str] = {}
        self._cursor: int | None = None

    def set_colors(self, colors: dict[str, str]) -> None:
        self._colors = colors

    def update_chart(self, history: HistoryData, title: str) -> None:
        self._history = history
        self._title = title
        self._cursor = None
        self._draw()

    def set_cursor(self, idx: int | None) -> None:
        self._cursor = idx
        self._draw()

    def show_empty(self, msg: str = "No data") -> None:
        self._history = None
        self._title = msg
        self._cursor = None
        self._draw()

    def on_resize(self) -> None:
        if self._history or self._title:
            self._draw()

    def _draw(self) -> None:
        plt = self.plt
        plt.clear_figure()
        plt.clear_data()
        plt.theme("clear")

        bg = self._colors.get("background", "#1e1e2e")
        fg = self._colors.get("foreground", "#cdd6f4")
        line_color = self._colors.get("accent", "#cba6f7")
        cursor_color = self._colors.get("foreground", "#cdd6f4")

        plt.canvas_color(bg)
        plt.axes_color(bg)
        plt.ticks_color(fg)

        if not self._history or not self._history.closes:
            plt.title(self._title)
            self.refresh()
            return

        h = self._history
        x = list(range(len(h.closes)))
        plt.plot(x, h.closes, color=line_color)

        # Cursor vertical line
        if self._cursor is not None and 0 <= self._cursor < len(h.closes):
            plt.vline(self._cursor, color=cursor_color)

        # Date labels on x-axis
        n = len(h.dates)
        step = max(1, n // 6)
        label_indices = list(range(0, n, step))
        if n - 1 not in label_indices:
            label_indices.append(n - 1)

        labels = []
        for i in label_indices:
            dt = h.dates[i]
            if n < 100 and (h.dates[-1] - h.dates[0]).days < 2:
                labels.append(dt.strftime("%H:%M"))
            else:
                labels.append(dt.strftime("%b %d"))

        plt.xticks(label_indices, labels)
        plt.title(self._title)
        self.refresh()

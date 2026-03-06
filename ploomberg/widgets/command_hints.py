"""Bottom command hint bar, Midnight Commander style."""

from __future__ import annotations

from textual.widgets import Static


class CommandHints(Static):
    DEFAULT_CSS = """
    CommandHints {
        height: 1;
        width: 100%;
        dock: bottom;
        background: $surface;
        color: $text;
        text-align: center;
    }
    """

    def __init__(self, hints: str, **kwargs) -> None:
        super().__init__(hints, **kwargs)

"""Built-in theme definitions for Ploomberg."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    name: str
    background: str
    foreground: str
    price_up: str
    price_down: str
    price_flat: str
    header: str
    border: str
    accent: str



BUILTIN_THEMES: dict[str, Theme] = {
    "catppuccin-mocha": Theme(
        name="Catppuccin Mocha",
        background="#1e1e2e",
        foreground="#cdd6f4",
        price_up="#a6e3a1",
        price_down="#f38ba8",
        price_flat="#f9e2af",
        header="#89b4fa",
        border="#585b70",
        accent="#cba6f7",
    ),
    "bloomberg": Theme(
        name="Bloomberg Classic",
        background="#000000",
        foreground="#ff8c00",
        price_up="#00ff00",
        price_down="#ff0000",
        price_flat="#ffff00",
        header="#ff8c00",
        border="#333333",
        accent="#ff8c00",
    ),
    "solarized": Theme(
        name="Solarized Dark",
        background="#002b36",
        foreground="#839496",
        price_up="#859900",
        price_down="#dc322f",
        price_flat="#b58900",
        header="#268bd2",
        border="#586e75",
        accent="#2aa198",
    ),
    "gruvbox": Theme(
        name="Gruvbox",
        background="#282828",
        foreground="#ebdbb2",
        price_up="#b8bb26",
        price_down="#fb4934",
        price_flat="#fabd2f",
        header="#83a598",
        border="#504945",
        accent="#d3869b",
    ),
    "nord": Theme(
        name="Nord",
        background="#2e3440",
        foreground="#d8dee9",
        price_up="#a3be8c",
        price_down="#bf616a",
        price_flat="#ebcb8b",
        header="#88c0d0",
        border="#4c566a",
        accent="#b48ead",
    ),
}

DEFAULT_THEME = "catppuccin-mocha"

"""Configuration management for Ploomberg."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "ploomberg"
CONFIG_FILE = CONFIG_DIR / "config.json"

# All available assets with their provider mappings
AVAILABLE_ASSETS: dict[str, dict] = {
    "XAU": {"name": "Gold", "provider": "metals", "symbol": "XAU", "unit": "oz"},
    "XAG": {"name": "Silver", "provider": "metals", "symbol": "XAG", "unit": "oz"},
    "XCU": {"name": "Copper", "provider": "yahoo", "symbol": "HG=F", "unit": "lb"},
    "NI": {"name": "Nickel", "provider": "yahoo", "symbol": "NICK.L", "unit": "mt"},
    "ZN": {"name": "Zinc", "provider": "yahoo", "symbol": "ZINC.L", "unit": "mt"},
    "CL": {"name": "Crude Oil", "provider": "yahoo", "symbol": "CL=F", "unit": "bbl"},
    "NG": {"name": "Natural Gas", "provider": "yahoo", "symbol": "NG=F", "unit": "mmBtu"},
    "EUR": {"name": "EUR/USD", "provider": "frankfurter", "symbol": "EUR", "unit": ""},
    "BTC": {"name": "BTC/USD", "provider": "coingecko", "symbol": "bitcoin", "unit": ""},
}

DEFAULT_WATCHLIST = ["XAU", "XAG", "XCU", "NI", "ZN", "CL", "NG", "EUR", "BTC"]

# Special watchlist entry that renders as a visual separator line
SEPARATOR = "---"


@dataclass
class PloombergConfig:
    watchlist: list[str] = field(default_factory=lambda: list(DEFAULT_WATCHLIST))
    hidden_assets: list[str] = field(default_factory=list)
    custom_assets: dict[str, dict] = field(default_factory=dict)
    theme: str = "catppuccin-mocha"
    refresh_interval: int = 60


def register_custom_assets(config: PloombergConfig) -> None:
    """Merge custom_assets into AVAILABLE_ASSETS so providers can find them."""
    for asset_id, info in config.custom_assets.items():
        if asset_id not in AVAILABLE_ASSETS:
            AVAILABLE_ASSETS[asset_id] = info


def load_config() -> PloombergConfig:
    """Load config from disk, or return defaults."""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return PloombergConfig(**data)
        except (json.JSONDecodeError, TypeError):
            pass
    return PloombergConfig()


def save_config(config: PloombergConfig) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), indent=2))

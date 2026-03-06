"""Base provider interface and shared data model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AssetPrice:
    symbol: str
    name: str
    price: float
    change_pct: float
    last_updated: datetime
    provider: str


class PriceProvider(ABC):
    """Abstract base for all price data providers."""

    @abstractmethod
    async def fetch_prices(self, symbols: list[str]) -> dict[str, AssetPrice]:
        """Fetch current prices for the given symbols.

        Returns a dict mapping asset ID to AssetPrice.
        """
        ...

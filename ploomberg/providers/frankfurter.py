"""Frankfurter API provider for forex rates."""

from __future__ import annotations

from datetime import datetime

import httpx

from ploomberg.providers.base import AssetPrice, PriceProvider


class FrankfurterProvider(PriceProvider):
    """Fetches forex rates from Frankfurter (ECB data). No API key needed."""

    BASE_URL = "https://api.frankfurter.app"

    async def fetch_prices(self, symbols: list[str]) -> dict[str, AssetPrice]:
        results: dict[str, AssetPrice] = {}
        currencies = [s for s in symbols if s in ("EUR", "GBP", "JPY", "CHF", "CAD", "AUD")]
        if not currencies:
            return results

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/latest",
                    params={"from": "USD", "to": ",".join(currencies)},
                )
                resp.raise_for_status()
                data = resp.json()

                now = datetime.now()
                rates = data.get("rates", {})

                for symbol in currencies:
                    if symbol in rates:
                        rate = rates[symbol]
                        results[symbol] = AssetPrice(
                            symbol=symbol,
                            name=f"{symbol}/USD",
                            price=rate,
                            change_pct=0.0,
                            last_updated=now,
                            provider="frankfurter",
                        )
        except (httpx.HTTPError, KeyError, ValueError):
            pass

        return results

"""CoinGecko API provider for cryptocurrency prices."""

from __future__ import annotations

from datetime import datetime

import httpx

from ploomberg.providers.base import AssetPrice, PriceProvider

# Map our asset IDs to CoinGecko IDs
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "DOGE": "dogecoin",
}


class CoinGeckoProvider(PriceProvider):
    """Fetches crypto prices from CoinGecko. No API key needed (public tier)."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    async def fetch_prices(self, symbols: list[str]) -> dict[str, AssetPrice]:
        results: dict[str, AssetPrice] = {}
        gecko_ids = {s: COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS}
        if not gecko_ids:
            return results

        try:
            ids_param = ",".join(gecko_ids.values())
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/simple/price",
                    params={
                        "ids": ids_param,
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                now = datetime.now()
                for asset_id, gecko_id in gecko_ids.items():
                    if gecko_id in data:
                        coin = data[gecko_id]
                        results[asset_id] = AssetPrice(
                            symbol=asset_id,
                            name=f"{asset_id}/USD",
                            price=coin.get("usd", 0.0),
                            change_pct=coin.get("usd_24h_change", 0.0),
                            last_updated=now,
                            provider="coingecko",
                        )
        except (httpx.HTTPError, KeyError, ValueError):
            pass

        return results

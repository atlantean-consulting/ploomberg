"""Metals price provider using Yahoo Finance for gold and silver."""

from __future__ import annotations

import asyncio
from datetime import datetime

from ploomberg.providers.base import AssetPrice, PriceProvider

METAL_TICKERS = {
    "XAU": ("GC=F", "Gold"),
    "XAG": ("SI=F", "Silver"),
}


class MetalsProvider(PriceProvider):
    """Fetches precious metal prices via Yahoo Finance futures."""

    async def fetch_prices(self, symbols: list[str]) -> dict[str, AssetPrice]:
        results: dict[str, AssetPrice] = {}
        metals = {s: METAL_TICKERS[s] for s in symbols if s in METAL_TICKERS}
        if not metals:
            return results

        try:
            import yfinance as yf

            def _fetch():
                fetched = {}
                for asset_id, (ticker_sym, name) in metals.items():
                    try:
                        ticker = yf.Ticker(ticker_sym)
                        info = ticker.fast_info
                        price = info.last_price
                        prev_close = info.previous_close
                        if price and prev_close and prev_close != 0:
                            change_pct = ((price - prev_close) / prev_close) * 100
                        else:
                            change_pct = 0.0

                        fetched[asset_id] = AssetPrice(
                            symbol=asset_id,
                            name=name,
                            price=float(price) if price else 0.0,
                            change_pct=round(change_pct, 2),
                            last_updated=datetime.now(),
                            provider="yahoo",
                        )
                    except Exception:
                        pass
                return fetched

            results = await asyncio.to_thread(_fetch)
        except ImportError:
            pass

        return results

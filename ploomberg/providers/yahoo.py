"""Yahoo Finance fallback provider for commodities and industrial metals."""

from __future__ import annotations

import asyncio
from datetime import datetime

from ploomberg.providers.base import AssetPrice, PriceProvider

# Map our asset IDs to Yahoo Finance ticker symbols
YAHOO_TICKERS = {
    "XCU": ("HG=F", "Copper"),
    "NI": ("NICK.L", "Nickel"),
    "ZN": ("ZINC.L", "Zinc"),
    "CL": ("CL=F", "Crude Oil"),
    "NG": ("NG=F", "Natural Gas"),
}


class YahooProvider(PriceProvider):
    """Fetches commodity prices via yfinance (Yahoo Finance)."""

    async def fetch_prices(self, symbols: list[str]) -> dict[str, AssetPrice]:
        from ploomberg.config import AVAILABLE_ASSETS

        results: dict[str, AssetPrice] = {}
        tickers: dict[str, tuple[str, str]] = {}
        for s in symbols:
            if s in YAHOO_TICKERS:
                tickers[s] = YAHOO_TICKERS[s]
            elif s in AVAILABLE_ASSETS and AVAILABLE_ASSETS[s].get("provider") == "yahoo":
                info = AVAILABLE_ASSETS[s]
                tickers[s] = (info["symbol"], info["name"])
        if not tickers:
            return results

        try:
            import yfinance as yf

            # yfinance is sync, run in executor
            def _fetch():
                fetched = {}
                for asset_id, (ticker_sym, name) in tickers.items():
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

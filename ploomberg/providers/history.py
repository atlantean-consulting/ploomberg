"""Historical price data fetcher for chart view."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx


@dataclass
class HistoryData:
    dates: list[datetime]
    closes: list[float]
    highs: list[float]
    lows: list[float]
    volumes: list[float]


# Period definitions: (label, yfinance_period, days_for_api)
PERIODS = [
    ("1D", "1d", 1),
    ("5D", "5d", 5),
    ("1M", "1mo", 30),
    ("3M", "3mo", 90),
    ("6M", "6mo", 180),
    ("1Y", "1y", 365),
]


async def fetch_history(asset_id: str, period_idx: int) -> HistoryData | None:
    """Fetch historical price data for the given asset and period."""
    from ploomberg.config import AVAILABLE_ASSETS

    info = AVAILABLE_ASSETS.get(asset_id)
    if not info:
        return None

    provider = info["provider"]
    _, yf_period, days = PERIODS[period_idx]

    if provider == "metals":
        from ploomberg.providers.metals import METAL_TICKERS
        ticker_sym = METAL_TICKERS.get(asset_id, (info["symbol"],))[0]
        return await _fetch_yfinance(ticker_sym, yf_period)
    elif provider == "yahoo":
        return await _fetch_yfinance(info["symbol"], yf_period)
    elif provider == "frankfurter":
        return await _fetch_frankfurter(info["symbol"], days)
    elif provider == "coingecko":
        from ploomberg.providers.coingecko import COINGECKO_IDS
        gecko_id = COINGECKO_IDS.get(asset_id)
        if gecko_id:
            return await _fetch_coingecko(gecko_id, days)

    return None


async def _fetch_yfinance(ticker_sym: str, period: str) -> HistoryData | None:
    """Fetch history via yfinance (sync, run in thread)."""
    try:
        import yfinance as yf

        def _fetch():
            ticker = yf.Ticker(ticker_sym)
            # Use interval appropriate to period
            interval = "5m" if period == "1d" else "1d"
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                return None
            return HistoryData(
                dates=[dt.to_pydatetime() for dt in hist.index],
                closes=hist["Close"].tolist(),
                highs=hist["High"].tolist(),
                lows=hist["Low"].tolist(),
                volumes=hist["Volume"].tolist() if "Volume" in hist.columns else [0.0] * len(hist),
            )

        return await asyncio.to_thread(_fetch)
    except Exception:
        return None


async def _fetch_frankfurter(symbol: str, days: int) -> HistoryData | None:
    """Fetch forex history from Frankfurter timeseries API."""
    try:
        end = datetime.now()
        start = end - timedelta(days=max(days, 2))
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                f"https://api.frankfurter.app/{start:%Y-%m-%d}..{end:%Y-%m-%d}",
                params={"from": "USD", "to": symbol},
            )
            resp.raise_for_status()
            data = resp.json()

        rates = data.get("rates", {})
        dates = sorted(rates.keys())
        closes = [rates[d][symbol] for d in dates]
        dts = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
        return HistoryData(
            dates=dts,
            closes=closes,
            highs=closes,
            lows=closes,
            volumes=[0.0] * len(closes),
        )
    except Exception:
        return None


async def _fetch_coingecko(gecko_id: str, days: int) -> HistoryData | None:
    """Fetch crypto history from CoinGecko market_chart API."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{gecko_id}/market_chart",
                params={"vs_currency": "usd", "days": str(days)},
            )
            resp.raise_for_status()
            data = resp.json()

        prices = data.get("prices", [])
        if not prices:
            return None

        dates = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
        closes = [p[1] for p in prices]
        return HistoryData(
            dates=dates,
            closes=closes,
            highs=closes,
            lows=closes,
            volumes=[0.0] * len(closes),
        )
    except Exception:
        return None

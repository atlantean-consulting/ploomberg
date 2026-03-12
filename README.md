# Ploomberg v0.67

"Oh my Gods, what's he gone and done *this* time?"

I have for you a Bloomberg Terminal-inspired commodity and currency tracker for your command line. It's built with Python and [Textual](https://textual.textualize.io/).

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          P L O O M B E R G  v0.67                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┃  ▲ Gold           $2,648.30     +1.24%           ┃
┃  ▼ Silver            $31.42     -0.38%           ┃
┃  ▲ Crude Oil         $68.91     +0.67%           ┃
┃  ▲ BTC/USD       $83,241.00     +2.15%           ┃
```

## What It Does

- **Live Dashboard** (F1) — real-time price ticker for commodities, metals, forex, and crypto
- **Converter** (F2) — currency and commodity unit converter with live rates
- **Charts** (F3) — interactive historical price charts with cursor, multiple timeframes
- **Silver Stash** (F4) — track your physical silver holdings, DCA log, hypothetical calculator
- **Paper Trading** (F6) — simulated trading with $10k virtual cash, portfolio P&L tracking
- **Dashboard Editor** (F5) — add, remove, reorder, hide assets; insert visual separators
- **Theme Editor** (F7) — five built-in themes with live preview

## Install

```bash
git clone <this-repo>
cd ploomberg
pip install -e .
```

## Run

```bash
python -m ploomberg
```

## Requirements

- Python 3.10+
- No API keys needed — all data sources are free/public

## Data Sources

| Source | Covers | Auth |
|--------|--------|------|
| [Frankfurter](https://api.frankfurter.app) | Forex (EUR/USD) | None |
| [CoinGecko](https://api.coingecko.com) | Crypto (BTC) | None |
| [Yahoo Finance](https://pypi.org/project/yfinance/) | Metals, commodities, equities | None |

## Quick Keys

| Key | Screen |
|-----|--------|
| F1 | Dashboard |
| F2 | Converter |
| F3 | Charts |
| F4 | Silver Stash |
| F5 | Editor |
| F6 | Paper Trading |
| F7 | Themes |
| Q | Quit |

See [MANUAL.md](MANUAL.md) for the full reference.

## License

GNU GPL v3, with an additional caveat:

*This is not financial advice.*

Again:

THIS IS NOT FINANCIAL ADVICE.

The stock market is a legalized casino backed by the full faith and credit of the government.

Don't blame us if you paper-trade your way to imaginary bankruptcy.

*Definitely* don't blame us if you use any information you gleaned from this app to real-life-trade your way into real-life-bankruptcy.

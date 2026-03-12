# Ploomberg v0.67 Manual

## Table of Contents

1. [Installation](#installation)
2. [Dashboard (F1)](#dashboard-f1)
3. [Converter (F2)](#converter-f2)
4. [Charts (F3)](#charts-f3)
5. [Silver Stash (F4)](#silver-stash-f4)
6. [Dashboard Editor (F5)](#dashboard-editor-f5)
7. [Paper Trading (F6)](#paper-trading-f6)
8. [Theme Editor (F7)](#theme-editor-f7)
9. [Data Sources](#data-sources)
10. [Configuration](#configuration)
11. [CLI Tools](#cli-tools)
12. [Complete Key Reference](#complete-key-reference)

---

## Installation

```bash
git clone <repo-url>
cd ploomberg
pip install -e .
python -m ploomberg
```

**Requirements:** Python 3.10+, no API keys needed.

**Dependencies:** textual, httpx, yfinance, textual-plotext (all installed automatically).

---

## Dashboard (F1)

The main screen. Displays a live price ticker for all assets on your watchlist, refreshing every 60 seconds.

Each row shows:
- **Direction arrow** — green up-triangle, red down-triangle, or yellow dash
- **Asset name**
- **Current price** in USD
- **24-hour change** — percentage by default, toggle to dollar amounts with `P`

The status bar at the bottom shows:
- Current time (ISO format with timezone)
- Last data refresh timestamp
- Countdown to next refresh
- Market status indicators: **NY** (NYSE), **GB** (LSE), **JP** (TSE) — green if open, yellow if closing within 1 hour, red if closed
- Connection indicator dot — green when online, red when offline

### Dashboard Keys

| Key | Action |
|-----|--------|
| R | Force an immediate price refresh |
| P | Toggle 24H change between % and $ |

**Rate limiting:** Pressing `R` twice within 30 seconds shows a warning. A third press triggers a 30-second "TILT" lockout to prevent API abuse.

---

## Converter (F2)

A currency and commodity unit converter. Enter an amount, select a "from" and "to" asset, and get a live conversion using the most recent fetched prices.

---

## Charts (F3)

Interactive historical price charts powered by plotext. Select any asset from your watchlist and view its price history across multiple timeframes.

### Chart Keys

| Key | Action |
|-----|--------|
| Left/Right | Move cursor across the chart |
| PgUp/PgDn | Jump cursor 10% of chart width |
| Home/End | Move cursor to start/end |
| Esc | Clear cursor |
| Up/Down | Cycle through assets |
| +/- | Change timeframe |
| 1 | 1 Day |
| 2 | 5 Days |
| 3 | 1 Month |
| 4 | 3 Months |
| 5 | 6 Months |
| 6 | 1 Year |

The detail panel on the right shows the exact date, price, and change at the cursor position.

---

## Silver Stash (F4)

A dedicated tracker for physical silver holdings. Designed for dollar-cost averaging (DCA) strategies.

### Sections

- **Stash Summary** — total holdings (troy oz), total cost, average cost per oz, current market value, unrealized P&L (updated live from spot price)
- **Hypothetical Calculator** — type any price-per-oz to see what your holdings would be worth
- **Purchase Log** — chronological list of all recorded purchases with date, ounces, price, cost, and notes

### Importing Purchase Data

Use the CLI import tool:

```bash
ploomberg-import purchases.csv
```

CSV format (headers required):

```csv
date,ounces,price_per_oz,note
2024-01-15,10.5,28.50,January buy
2024-02-01,5.0,29.10,
```

The `note` column is optional. Use `--replace` to overwrite existing data instead of appending.

---

## Dashboard Editor (F5)

Manage which assets appear on your dashboard and in what order.

### Editor Keys

| Key | Action |
|-----|--------|
| PgUp/PgDn | Move selected asset up/down in the list |
| H | Toggle hide/unhide (hidden assets stay in config but don't show on dashboard) |
| D | Delete asset from watchlist entirely |
| A | Add a new asset (opens asset picker) |
| S | Insert a visual separator line below the current selection |

**Separators** appear as horizontal rules on the dashboard, letting you group assets visually (e.g., metals above the line, energy below). They can be reordered and deleted just like assets.

---

## Paper Trading (F6)

A simulated trading environment for experimenting with strategies using virtual money. You start with **$10,000** in cash.

### Sections

- **Portfolio Summary** — cash balance, invested value, total portfolio value, total return ($ and %)
- **Open Positions** — each held asset with quantity, average cost basis, current price, market value, and unrealized P&L
- **Execute Trade** — enter a ticker symbol directly OR select from your watchlist dropdown, set a quantity, then execute
- **Trade History** — chronological log of all trades (most recent first, last 20 shown)

### Trading Keys

| Key | Action |
|-----|--------|
| F9 | Buy — purchase the selected asset at the current market price |
| F10 | Sell — sell the selected asset at the current market price |
| F12 | Reset — wipe the portfolio and start over with $10,000 |

### How Trading Works

1. Select an asset using the **Ticker** text input (type any asset ID like `XAU`, `BTC`, etc.) or the **Watchlist** dropdown
2. Enter a quantity in the **Quantity** field
3. Press **F9** to buy or **F10** to sell

Trades execute at the most recent market price. The ticker input takes priority over the dropdown if both are filled. Assets must be on your watchlist (and have a streaming price) to trade.

All portfolio data persists across sessions in `~/.config/ploomberg/paper_trading.json`.

---

## Theme Editor (F7)

Browse and apply visual themes with a live preview. Five built-in themes:

| Theme | Style |
|-------|-------|
| catppuccin-mocha | Warm dark pastels (default) |
| bloomberg | Classic terminal orange-on-black |
| solarized | Ethan Schoonover's balanced palette |
| gruvbox | Retro earthy tones |
| nord | Arctic cool blues |

Navigate with arrow keys, press **Enter** to apply. The theme persists across sessions.

---

## Data Sources

All data sources are free and require no API keys.

| Provider | API | Assets | Rate Limits |
|----------|-----|--------|-------------|
| Frankfurter | api.frankfurter.app | Forex (EUR/USD) | Generous, no key |
| CoinGecko | api.coingecko.com/api/v3 | Crypto (BTC/USD) | 5-15 calls/min |
| Yahoo Finance | yfinance Python library | Metals (Gold, Silver), Energy (Crude, Nat Gas), Industrial (Copper, Nickel, Zinc), Equities | No hard limit |

Prices refresh automatically every 60 seconds.

---

## Configuration

All configuration is stored in `~/.config/ploomberg/`:

| File | Contents |
|------|----------|
| `config.json` | Watchlist, hidden assets, custom assets, theme selection, refresh interval |
| `stash.json` | Silver stash purchase records |
| `paper_trading.json` | Paper trading portfolio (cash, trade history) |

The config is managed automatically through the UI. You generally don't need to edit these files by hand, but they're plain JSON if you want to.

### Default Watchlist

Gold (XAU), Silver (XAG), Copper (XCU), Nickel (NI), Zinc (ZN), Crude Oil (CL), Natural Gas (NG), EUR/USD (EUR), BTC/USD (BTC).

---

## CLI Tools

### ploomberg

```bash
python -m ploomberg    # or just: ploomberg
```

Launches the terminal UI.

### ploomberg-import

```bash
ploomberg-import <file.csv> [--replace]
```

Import silver purchase records from a CSV file into the stash tracker. Without `--replace`, new records are appended to existing data.

---

## Complete Key Reference

### Global (available on all screens)

| Key | Action |
|-----|--------|
| F1 | Switch to Dashboard |
| F2 | Switch to Converter |
| F3 | Switch to Charts |
| F4 | Switch to Silver Stash |
| F5 | Switch to Dashboard Editor |
| F6 | Switch to Paper Trading |
| F7 | Switch to Theme Editor |
| Q | Quit |

### Dashboard (F1)

| Key | Action |
|-----|--------|
| R | Force refresh |
| P | Toggle 24H change between % and $ |

### Charts (F3)

| Key | Action |
|-----|--------|
| Left/Right | Move cursor |
| PgUp/PgDn | Jump cursor 10% |
| Home/End | Cursor to start/end |
| Esc | Clear cursor |
| Up/Down | Cycle assets |
| +/- | Change timeframe |
| 1-6 | Jump to specific timeframe |

### Editor (F5)

| Key | Action |
|-----|--------|
| PgUp/PgDn | Reorder |
| H | Hide/unhide |
| D | Delete |
| A | Add asset |
| S | Insert separator |

### Paper Trading (F6)

| Key | Action |
|-----|--------|
| F9 | Buy |
| F10 | Sell |
| F12 | Reset portfolio |

### Theme Editor (F7)

| Key | Action |
|-----|--------|
| Enter | Apply selected theme |

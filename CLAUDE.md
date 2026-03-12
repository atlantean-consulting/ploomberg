# Ploomberg

Bloomberg Terminal-inspired command-line commodity & currency tracker built with Python + Textual.

## Quick Start

```bash
cd /home/pf183229/code/ploomberg
pip install -e .
python -m ploomberg
```

## Project Structure

```
ploomberg/
├── __main__.py              # Entry point (calls PloombergApp().run())
├── app.py                   # PloombergApp — main Textual App subclass
├── config.py                # Config management, asset registry, persistence
├── import_cli.py            # CLI tool: ploomberg-import <file.csv> [--replace]
├── messages.py              # Custom Textual messages (PriceUpdate, AssetAdded, etc.)
├── paper_trading.py         # Paper trading data model, persistence (~/.config/ploomberg/paper_trading.json)
├── stash.py                 # Silver stash data model, persistence (~/.config/ploomberg/stash.json), CSV import
├── themes.py                # 5 built-in theme dataclasses (catppuccin-mocha, bloomberg, solarized, gruvbox, nord)
├── providers/
│   ├── base.py              # AssetPrice dataclass + PriceProvider ABC
│   ├── frankfurter.py       # Forex rates (EUR) — api.frankfurter.app, no key needed
│   ├── coingecko.py         # Crypto (BTC) — api.coingecko.com, no key needed
│   ├── metals.py            # Gold/Silver — via yfinance (GC=F, SI=F)
│   ├── yahoo.py             # Copper, Nickel, Zinc, Crude Oil, Nat Gas — via yfinance
│   └── history.py           # Historical price data fetcher (yfinance, Frankfurter timeseries, CoinGecko market_chart)
├── screens/
│   ├── dashboard_view.py    # F1 — main ticker dashboard
│   ├── converter_view.py    # F2 — currency/commodity converter
│   ├── chart_view.py        # F3 — historical price charts with interactive cursor
│   ├── stash_view.py        # F4 — silver stash tracker (holdings, DCA, hypothetical calc)
│   ├── trading_view.py      # F6 — paper trading simulator (buy/sell, portfolio, P&L)
│   ├── editor_view.py       # F5 — add/remove dashboard assets
│   └── theme_view.py        # F7 — theme picker with live preview
└── widgets/
    ├── header_bar.py        # Top branding bar ("P L O O M B E R G")
    ├── ticker_table.py      # Price table with directional arrows and color-coded changes
    ├── status_bar.py        # ISO clock │ data freshness │ countdown │ market indicators │ online dot
    ├── command_hints.py     # Bottom MC-style key hints (docked)
    ├── converter_form.py    # Amount/From/To inputs with live calculation
    ├── price_chart.py       # PlotextPlot wrapper with cursor line support
    ├── stash_table.py       # Silver stash display: summary, hypothetical calc, purchase log
    ├── trading_panel.py     # Paper trading display: portfolio summary, positions, trade form, history
    └── theme_preview.py     # Sample rows showing theme colors
```

## Architecture & Patterns

### Textual Conventions (mirrors LINAMP in ./linamp-exmaple/)
- **Mode switching**: `App.MODES` dict maps names to Screen classes; `switch_mode()` navigates between them
- **Message broadcasting**: App polls providers every 60s, posts `PriceUpdate` to `self.screen` which delegates to child widgets
- **CSS theming**: `get_css_variables()` override injects theme colors as CSS variables (`$background`, `$success`, `$error`, etc.); `refresh_css()` applies changes at runtime
- **Async list refresh**: `ListView.clear()` and `ListView.append()` are async in Textual 8 — always `await` them to avoid `DuplicateIds` errors

### Data Flow
1. `PloombergApp.on_mount()` starts a 1-second interval timer (`_tick`)
2. `_tick` decrements countdown; at zero, calls `_poll_prices()`
3. `_poll_prices()` groups watchlist assets by provider, fetches all concurrently via `asyncio.gather()`
4. Results stored in `self.prices`, then `_broadcast_prices()` posts `PriceUpdate` to current screen
5. Screen's `on_price_update()` handler calls `widget.update_prices(prices)` on its children
6. Mode switch actions also call `_broadcast_prices()` so prices appear immediately on navigation

### Provider Details
| Provider | API | Assets | Auth | Notes |
|----------|-----|--------|------|-------|
| FrankfurterProvider | api.frankfurter.app | EUR (forex) | None | Use `from`/`to` params, NOT `base`/`symbols`. Domain is `.app` not `.dev` |
| CoinGeckoProvider | api.coingecko.com/api/v3 | BTC (crypto) | None (public) | 5-15 calls/min unauthenticated |
| MetalsProvider | yfinance | XAU (GC=F), XAG (SI=F) | None | Frankfurter does NOT support XAU/XAG |
| YahooProvider | yfinance | XCU (HG=F), NI (NICK.L), ZN (ZINC.L), CL (CL=F), NG (NG=F) | None | Nickel/Zinc use London ETF tickers |

### Status Bar Market Indicators
- NY (America/New_York): 9:30-16:00 local, DST-aware
- GB (Europe/London): 8:00-16:30 local, DST-aware
- JP (Asia/Tokyo): 9:00-15:00 local, no DST (lunch break not modeled)
- Colors: green=open, yellow=closing within 1hr, red=closed; weekends always red

### Config
- Persisted at `~/.config/ploomberg/config.json`
- Fields: `watchlist` (list of asset IDs), `theme` (theme ID string), `refresh_interval` (seconds)
- Asset registry in `config.py` `AVAILABLE_ASSETS` dict maps asset IDs to provider/symbol/name
- Watchlist supports `"---"` sentinel entries as visual separators (rendered as horizontal rules in ticker table)
- Stash data persisted at `~/.config/ploomberg/stash.json` (purchase records for silver tracker)
- Paper trading data persisted at `~/.config/ploomberg/paper_trading.json` (portfolio cash, trade history)

## Key Bindings
| Key | Action |
|-----|--------|
| F1 | Dashboard (default) |
| F2 | Converter |
| F3 | Chart |
| F4 | Silver Stash |
| F6 | Paper Trading |
| F5 | Dashboard Editor |
| F7 | Theme Editor |
| Q | Quit |
| R | Force refresh (in Dashboard) |
| P | Toggle 24H change %/$ (in Dashboard) |
| Space/Enter | Toggle asset (in Editor) |
| PgUp/PgDn | Reorder asset (in Editor) |
| H | Hide/unhide asset (in Editor) |
| D | Delete asset (in Editor) |
| A | Add asset (in Editor) |
| S | Insert separator (in Editor) |
| Enter | Apply theme (in Theme Editor) |
| Left/Right | Move cursor across chart (in Chart) |
| PgUp/PgDn | Jump cursor 10% (in Chart) |
| Home/End | Cursor to start/end (in Chart) |
| Esc | Clear cursor (in Chart) |
| Up/Down | Cycle assets (in Chart) |
| +/- | Change period (in Chart) |
| 1-6 | Jump to period 1D/5D/1M/3M/6M/1Y (in Chart) |
| F9 | Buy (in Paper Trading) |
| F10 | Sell (in Paper Trading) |
| F12 | Reset portfolio (in Paper Trading) |

## Dependencies
- `textual>=0.47.0` (installed: 8.0.0)
- `httpx>=0.25.0`
- `yfinance>=0.2.0`
- `textual-plotext>=1.0.0` (plotext charts in Textual)
- Python 3.12

## Design Conventions
- Every view has: HeaderBar (top) → content → StatusBar → CommandHints (bottom, docked)
- Command hints are MC-style: `[bold]Key[/] Action` separated by double-space
- Catppuccin Mocha is the default theme; CSS uses Textual design variables ($success, $error, $warning, etc.)
- Ticker arrows: green ▲ positive, red ▼ negative, yellow ─ flat
- Ticker 24H change column toggles between % and $ via `P` key
- The reference project LINAMP is at `./linamp-exmaple/` (note: directory name has a typo, keep it as-is)

## Roadmap
- **Phase 1** (DONE): Dashboard ticker + Converter
- **Phase 1.5** (DONE): Theme Editor with 5 built-in themes
- **Phase 2** (DONE): Historical price charts (F3) with interactive cursor + detail panel
- **Phase 3** (DONE): Silver Stash tracker (F4) — holdings summary, DCA log, hypothetical calculator, CSV import
- **Phase 4** (DONE): Paper Trading simulator (F6) — virtual $10k cash, buy/sell at market prices, portfolio tracking, P&L, trade history
- **Phase 5** (TODO): Detail window — select an asset to view extended info (unit, exchange, provider, description, etc.)

## Gotchas & Lessons Learned
1. Frankfurter API is at `.app` not `.dev`, and uses `from`/`to` not `base`/`symbols`
2. Frankfurter only supports fiat currencies — no XAU/XAG/crypto
3. Yahoo Finance tickers for nickel/zinc: use `NICK.L` and `ZINC.L` (London ETFs), not S&P GSCI index tickers
4. `ListView.clear()` / `.append()` are async in Textual 8 — must await or you get DuplicateIds crashes
5. `get_css_variables()` is called during `super().__init__()`, so any instance attributes it depends on must be set BEFORE the super call
6. `_broadcast_prices()` must post to `self.screen` (the Screen object), not iterate `walk_children()` — the Screen has the `on_price_update` handler, child widgets do not
7. yfinance is synchronous — wrap calls in `asyncio.to_thread()` to avoid blocking the event loop
8. Metals config symbols (XAU, XAG) differ from yfinance tickers (GC=F, SI=F) — history fetcher must use `METAL_TICKERS` mapping, not raw config symbol
9. Textual `Input` widget requires `height: 3` (border + content + border) — `height: 1` renders the widget but leaves 0 content height, making it impossible to type
10. Don't use single-letter or `ctrl+` keybindings on screens that contain `Input` widgets — Input consumes printable chars and uses many ctrl combos (ctrl+a/e/d/w/u/f/k/x/c/v). Use function keys (F9, F10, etc.) instead
11. When building aligned columns with Rich markup (color tags), format the entire line as plain text first for correct Python alignment, then surgically inject `[color]...[/color]` around the target substring — f-string alignment counts markup characters as width

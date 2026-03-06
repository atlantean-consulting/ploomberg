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
├── messages.py              # Custom Textual messages (PriceUpdate, AssetAdded, etc.)
├── themes.py                # 5 built-in theme dataclasses (catppuccin-mocha, bloomberg, solarized, gruvbox, nord)
├── providers/
│   ├── base.py              # AssetPrice dataclass + PriceProvider ABC
│   ├── frankfurter.py       # Forex rates (EUR) — api.frankfurter.app, no key needed
│   ├── coingecko.py         # Crypto (BTC) — api.coingecko.com, no key needed
│   ├── metals.py            # Gold/Silver — via yfinance (GC=F, SI=F)
│   └── yahoo.py             # Copper, Nickel, Zinc, Crude Oil, Nat Gas — via yfinance
├── screens/
│   ├── dashboard_view.py    # F1 — main ticker dashboard
│   ├── converter_view.py    # F2 — currency/commodity converter
│   ├── editor_view.py       # F5 — add/remove dashboard assets
│   └── theme_view.py        # F7 — theme picker with live preview
└── widgets/
    ├── header_bar.py        # Top branding bar ("P L O O M B E R G")
    ├── ticker_table.py      # Price table with directional arrows and color-coded changes
    ├── status_bar.py        # ISO clock │ data freshness │ countdown │ market indicators │ online dot
    ├── command_hints.py     # Bottom MC-style key hints (docked)
    ├── converter_form.py    # Amount/From/To inputs with live calculation
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

## Key Bindings
| Key | Action |
|-----|--------|
| F1 | Dashboard (default) |
| F2 | Converter |
| F5 | Dashboard Editor |
| F7 | Theme Editor |
| Q | Quit |
| Space/Enter | Toggle asset (in Editor) |
| Enter | Apply theme (in Theme Editor) |

## Dependencies
- `textual>=0.47.0` (installed: 8.0.0)
- `httpx>=0.25.0`
- `yfinance>=0.2.0`
- Python 3.12

## Design Conventions
- Every view has: HeaderBar (top) → content → StatusBar → CommandHints (bottom, docked)
- Command hints are MC-style: `[bold]Key[/] Action` separated by double-space
- Catppuccin Mocha is the default theme; CSS uses Textual design variables ($success, $error, $warning, etc.)
- Ticker arrows: green ▲ positive, red ▼ negative, yellow ─ flat
- The reference project LINAMP is at `./linamp-exmaple/` (note: directory name has a typo, keep it as-is)

## Roadmap
- **Phase 1** (DONE): Dashboard ticker + Converter
- **Phase 1.5** (DONE): Theme Editor with 5 built-in themes
- **Phase 2** (TODO): Historical price charts (F3)
- **Phase 3** (TODO): Watchlists (F4)
- **Phase 4** (TODO): Detail window — select an asset to view extended info (unit, exchange, provider, description, etc.)

## Gotchas & Lessons Learned
1. Frankfurter API is at `.app` not `.dev`, and uses `from`/`to` not `base`/`symbols`
2. Frankfurter only supports fiat currencies — no XAU/XAG/crypto
3. Yahoo Finance tickers for nickel/zinc: use `NICK.L` and `ZINC.L` (London ETFs), not S&P GSCI index tickers
4. `ListView.clear()` / `.append()` are async in Textual 8 — must await or you get DuplicateIds crashes
5. `get_css_variables()` is called during `super().__init__()`, so any instance attributes it depends on must be set BEFORE the super call
6. `_broadcast_prices()` must post to `self.screen` (the Screen object), not iterate `walk_children()` — the Screen has the `on_price_update` handler, child widgets do not
7. yfinance is synchronous — wrap calls in `asyncio.to_thread()` to avoid blocking the event loop

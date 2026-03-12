"""Paper trading data model and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

TRADING_DIR = Path.home() / ".config" / "ploomberg"
TRADING_FILE = TRADING_DIR / "paper_trading.json"

DEFAULT_CASH = 10_000.00


@dataclass
class Trade:
    """A single paper trade."""

    timestamp: str  # ISO datetime
    asset_id: str
    side: str  # "buy" or "sell"
    quantity: float
    price: float

    @property
    def total(self) -> float:
        return self.quantity * self.price


@dataclass
class Position:
    """Aggregated position for a single asset."""

    asset_id: str
    quantity: float
    total_cost: float

    @property
    def avg_cost(self) -> float:
        return self.total_cost / self.quantity if self.quantity > 0 else 0.0

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def unrealized_pnl(self, price: float) -> float:
        return self.market_value(price) - self.total_cost


@dataclass
class Portfolio:
    """Paper trading portfolio with cash and trade history."""

    cash: float = DEFAULT_CASH
    initial_cash: float = DEFAULT_CASH
    trades: list[Trade] = field(default_factory=list)

    @property
    def positions(self) -> dict[str, Position]:
        """Aggregate trades into current positions."""
        pos: dict[str, Position] = {}
        for t in self.trades:
            if t.asset_id not in pos:
                pos[t.asset_id] = Position(t.asset_id, 0.0, 0.0)
            p = pos[t.asset_id]
            if t.side == "buy":
                p.total_cost += t.total
                p.quantity += t.quantity
            else:  # sell
                if p.quantity > 0:
                    # Reduce cost basis proportionally
                    cost_per_unit = p.total_cost / p.quantity
                    p.total_cost -= cost_per_unit * t.quantity
                p.quantity -= t.quantity
        # Remove closed positions
        return {k: v for k, v in pos.items() if abs(v.quantity) > 1e-9}

    def invested_value(self, prices: dict[str, float]) -> float:
        """Total market value of all positions."""
        total = 0.0
        for asset_id, pos in self.positions.items():
            price = prices.get(asset_id, 0.0)
            total += pos.market_value(price)
        return total

    def total_value(self, prices: dict[str, float]) -> float:
        """Cash + invested value."""
        return self.cash + self.invested_value(prices)

    def total_return(self, prices: dict[str, float]) -> float:
        """Return as dollar amount."""
        return self.total_value(prices) - self.initial_cash

    def total_return_pct(self, prices: dict[str, float]) -> float:
        """Return as percentage."""
        if self.initial_cash == 0:
            return 0.0
        return (self.total_return(prices) / self.initial_cash) * 100

    def can_buy(self, price: float, quantity: float) -> bool:
        return self.cash >= price * quantity

    def can_sell(self, asset_id: str, quantity: float) -> bool:
        pos = self.positions.get(asset_id)
        return pos is not None and pos.quantity >= quantity - 1e-9

    def execute_buy(self, asset_id: str, quantity: float, price: float) -> Trade:
        cost = quantity * price
        if cost > self.cash:
            raise ValueError(f"Insufficient cash: need ${cost:,.2f}, have ${self.cash:,.2f}")
        self.cash -= cost
        trade = Trade(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            asset_id=asset_id,
            side="buy",
            quantity=quantity,
            price=price,
        )
        self.trades.append(trade)
        return trade

    def execute_sell(self, asset_id: str, quantity: float, price: float) -> Trade:
        if not self.can_sell(asset_id, quantity):
            pos = self.positions.get(asset_id)
            have = pos.quantity if pos else 0.0
            raise ValueError(f"Insufficient holdings: have {have:.4f}, selling {quantity:.4f}")
        self.cash += quantity * price
        trade = Trade(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            asset_id=asset_id,
            side="sell",
            quantity=quantity,
            price=price,
        )
        self.trades.append(trade)
        return trade


def load_portfolio() -> Portfolio:
    """Load portfolio from disk, or return fresh portfolio."""
    try:
        data = json.loads(TRADING_FILE.read_text())
        trades = [Trade(**t) for t in data.get("trades", [])]
        return Portfolio(
            cash=data.get("cash", DEFAULT_CASH),
            initial_cash=data.get("initial_cash", DEFAULT_CASH),
            trades=trades,
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return Portfolio()


def save_portfolio(portfolio: Portfolio) -> None:
    """Persist portfolio to disk."""
    TRADING_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "cash": portfolio.cash,
        "initial_cash": portfolio.initial_cash,
        "trades": [asdict(t) for t in portfolio.trades],
    }
    TRADING_FILE.write_text(json.dumps(data, indent=2))

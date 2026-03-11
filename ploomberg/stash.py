"""Silver stash tracker — data model, persistence, and CSV import."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path

STASH_DIR = Path.home() / ".config" / "ploomberg"
STASH_FILE = STASH_DIR / "stash.json"


@dataclass
class Purchase:
    """A single silver purchase record."""

    date: str  # ISO format YYYY-MM-DD
    ounces: float
    price_per_oz: float  # USD paid per troy ounce
    note: str = ""

    @property
    def total_cost(self) -> float:
        return self.ounces * self.price_per_oz


@dataclass
class StashData:
    """All stash state persisted to disk."""

    purchases: list[Purchase] = field(default_factory=list)

    @property
    def total_ounces(self) -> float:
        return sum(p.ounces for p in self.purchases)

    @property
    def total_cost(self) -> float:
        return sum(p.total_cost for p in self.purchases)

    @property
    def avg_cost_per_oz(self) -> float:
        oz = self.total_ounces
        return self.total_cost / oz if oz else 0.0

    def current_value(self, spot_price: float) -> float:
        return self.total_ounces * spot_price

    def unrealized_pnl(self, spot_price: float) -> float:
        return self.current_value(spot_price) - self.total_cost

    def hypothetical_value(self, price_per_oz: float) -> float:
        return self.total_ounces * price_per_oz


def load_stash() -> StashData:
    """Load stash data from disk."""
    if STASH_FILE.exists():
        try:
            data = json.loads(STASH_FILE.read_text())
            purchases = [Purchase(**p) for p in data.get("purchases", [])]
            return StashData(purchases=purchases)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
    return StashData()


def save_stash(stash: StashData) -> None:
    """Persist stash data to disk."""
    STASH_DIR.mkdir(parents=True, exist_ok=True)
    data = {"purchases": [asdict(p) for p in stash.purchases]}
    STASH_FILE.write_text(json.dumps(data, indent=2))


def import_csv(path: str | Path) -> list[Purchase]:
    """Import purchases from a CSV file.

    Expected columns (header required):
        date        — YYYY-MM-DD
        ounces      — float, troy ounces purchased
        price_per_oz — float, USD price per troy ounce at time of purchase
        note        — (optional) free-text note

    Returns the list of parsed Purchase objects.
    Raises ValueError on malformed rows.
    """
    path = Path(path)
    purchases: list[Purchase] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)

        # Normalise headers: strip whitespace and lowercase
        if reader.fieldnames:
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        required = {"date", "ounces", "price_per_oz"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"CSV must have columns: {', '.join(sorted(required))}. "
                f"Found: {reader.fieldnames}"
            )

        for i, row in enumerate(reader, start=2):
            try:
                purchases.append(
                    Purchase(
                        date=row["date"].strip(),
                        ounces=float(row["ounces"]),
                        price_per_oz=float(row["price_per_oz"]),
                        note=row.get("note", "").strip(),
                    )
                )
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Row {i}: {exc}") from exc

    return purchases

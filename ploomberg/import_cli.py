"""CLI utility to import silver purchase data from CSV into the stash."""

from __future__ import annotations

import sys
from pathlib import Path

from ploomberg.stash import import_csv, load_stash, save_stash


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ploomberg-import <file.csv> [--replace]")
        print()
        print("Import silver purchase records from a CSV file.")
        print()
        print("CSV columns (header required):")
        print("  date          — YYYY-MM-DD")
        print("  ounces        — troy ounces purchased")
        print("  price_per_oz  — USD price per troy ounce")
        print("  note          — (optional) free-text note")
        print()
        print("Options:")
        print("  --replace     Replace all existing purchases (default: append)")
        sys.exit(1)

    csv_path = sys.argv[1]
    replace = "--replace" in sys.argv

    if not Path(csv_path).exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        new_purchases = import_csv(csv_path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    stash = load_stash()

    if replace:
        stash.purchases = new_purchases
        print(f"Replaced stash with {len(new_purchases)} purchase(s) from {csv_path}")
    else:
        stash.purchases.extend(new_purchases)
        print(f"Appended {len(new_purchases)} purchase(s) from {csv_path}")

    save_stash(stash)

    oz = stash.total_ounces
    cost = stash.total_cost
    avg = stash.avg_cost_per_oz
    print(f"  Total: {oz:,.3f} oz | Cost: ${cost:,.2f} | Avg: ${avg:,.2f}/oz")


if __name__ == "__main__":
    main()

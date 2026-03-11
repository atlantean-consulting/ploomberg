"""Silver stash display widget — holdings summary, purchase log, and hypothetical calculator."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static, Input
from textual.app import ComposeResult

from ploomberg.stash import StashData


def _fmt_usd(value: float) -> str:
    """Format as USD with commas."""
    return f"${value:,.2f}"


def _pnl_colored(pnl: float) -> str:
    if pnl > 0:
        return f"[green]+{_fmt_usd(pnl)}[/green]"
    elif pnl < 0:
        return f"[red]{_fmt_usd(pnl)}[/red]"
    return f"[yellow]{_fmt_usd(pnl)}[/yellow]"


class StashTable(Container):
    DEFAULT_CSS = """
    StashTable {
        height: 1fr;
        width: 100%;
        border: heavy $accent;
        padding: 0 1;
    }
    StashTable .stash-section-header {
        text-style: bold;
        color: $primary;
        height: 1;
        margin-top: 1;
    }
    StashTable .stash-separator {
        height: 1;
        color: $text-muted;
    }
    StashTable .stash-row {
        height: 1;
    }
    StashTable .stash-empty {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }
    StashTable .stash-purchase {
        height: 1;
    }
    StashTable #hypo-input {
        width: 20;
        height: 1;
        margin: 0 1;
    }
    StashTable .hypo-row {
        height: 1;
        layout: horizontal;
    }
    StashTable .hypo-label {
        height: 1;
        width: auto;
    }
    StashTable .hypo-result {
        height: 1;
        width: auto;
    }
    """

    def __init__(self, stash: StashData, **kwargs) -> None:
        super().__init__(**kwargs)
        self._stash = stash
        self._spot_price: float = 0.0

    def compose(self) -> ComposeResult:
        # --- Summary section ---
        yield Static("  STASH SUMMARY", classes="stash-section-header")
        yield Static("  " + "─" * 56, classes="stash-separator")
        yield Static("", id="summary-holdings", classes="stash-row")
        yield Static("", id="summary-cost", classes="stash-row")
        yield Static("", id="summary-avg", classes="stash-row")
        yield Static("", id="summary-value", classes="stash-row")
        yield Static("", id="summary-pnl", classes="stash-row")

        # --- What-if section ---
        yield Static("  HYPOTHETICAL CALCULATOR", classes="stash-section-header")
        yield Static("  " + "─" * 56, classes="stash-separator")
        yield Static(
            "  Enter price per oz to calculate hypothetical value:",
            classes="stash-row",
        )
        yield Input(placeholder="e.g. 50.00", id="hypo-input")
        yield Static("", id="hypo-result", classes="stash-row")

        # --- Purchase log ---
        yield Static("  PURCHASE LOG (DCA)", classes="stash-section-header")
        yield Static("  " + "─" * 56, classes="stash-separator")
        yield Static(
            "  DATE          OUNCES    $/OZ       COST       NOTE",
            classes="stash-row",
        )
        yield Static("  " + "─" * 56, classes="stash-separator")
        if not self._stash.purchases:
            yield Static(
                "  No purchases recorded. Import a CSV via: ploomberg-import <file.csv>",
                classes="stash-empty",
            )
        else:
            for i, p in enumerate(self._stash.purchases):
                note = p.note[:16] if p.note else ""
                yield Static(
                    f"  {p.date:<12}  {p.ounces:>8.3f}  {_fmt_usd(p.price_per_oz):>9}"
                    f"  {_fmt_usd(p.total_cost):>10}   {note}",
                    id=f"purchase-{i}",
                    classes="stash-purchase",
                )

    def on_mount(self) -> None:
        self._refresh_summary()

    def update_spot_price(self, price: float) -> None:
        """Called when we receive a new silver spot price."""
        self._spot_price = price
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        stash = self._stash
        oz = stash.total_ounces
        cost = stash.total_cost
        avg = stash.avg_cost_per_oz

        self.query_one("#summary-holdings", Static).update(
            f"  Total Holdings:  {oz:,.3f} troy oz"
        )
        self.query_one("#summary-cost", Static).update(
            f"  Total Cost:      {_fmt_usd(cost)}"
        )
        self.query_one("#summary-avg", Static).update(
            f"  Avg Cost / oz:   {_fmt_usd(avg)}"
        )

        if self._spot_price > 0:
            val = stash.current_value(self._spot_price)
            pnl = stash.unrealized_pnl(self._spot_price)
            self.query_one("#summary-value", Static).update(
                f"  Current Value:   {_fmt_usd(val)}  (@ {_fmt_usd(self._spot_price)}/oz spot)"
            )
            self.query_one("#summary-pnl", Static).update(
                f"  Unrealized P&L:  {_pnl_colored(pnl)}"
            )
        else:
            self.query_one("#summary-value", Static).update(
                "  Current Value:   [dim]waiting for spot price…[/dim]"
            )
            self.query_one("#summary-pnl", Static).update(
                "  Unrealized P&L:  [dim]---[/dim]"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Recalculate hypothetical value when user types a price."""
        result = self.query_one("#hypo-result", Static)
        text = event.value.strip()
        if not text:
            result.update("")
            return
        try:
            hypo_price = float(text)
        except ValueError:
            result.update("  [red]Enter a valid number[/red]")
            return

        oz = self._stash.total_ounces
        if oz == 0:
            result.update("  [dim]No holdings to calculate[/dim]")
            return

        hypo_val = self._stash.hypothetical_value(hypo_price)
        pnl = hypo_val - self._stash.total_cost
        result.update(
            f"  At {_fmt_usd(hypo_price)}/oz → Value: {_fmt_usd(hypo_val)}  "
            f"P&L: {_pnl_colored(pnl)}"
        )

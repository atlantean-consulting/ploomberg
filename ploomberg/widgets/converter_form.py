"""Currency/commodity conversion form widget."""

from __future__ import annotations

from textual.containers import Container, Vertical
from textual.widgets import Static, Input, Select
from textual.app import ComposeResult

from ploomberg.providers.base import AssetPrice
from ploomberg.config import AVAILABLE_ASSETS


# USD is always available as a base
CONVERTER_OPTIONS = [("USD", "US Dollar")] + [
    (aid, info["name"]) for aid, info in AVAILABLE_ASSETS.items()
]


class ConverterForm(Container):
    DEFAULT_CSS = """
    ConverterForm {
        height: 1fr;
        width: 100%;
        border: heavy $accent;
        padding: 1 2;
    }
    ConverterForm .form-label {
        height: 1;
        margin-top: 1;
    }
    ConverterForm Input {
        width: 40;
    }
    ConverterForm Select {
        width: 40;
    }
    ConverterForm .result-box {
        margin-top: 1;
        padding: 1 2;
        border: round $accent;
        height: auto;
    }
    ConverterForm .result-line {
        height: 1;
        text-style: bold;
    }
    ConverterForm .rate-line {
        height: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._prices: dict[str, AssetPrice] = {}

    def compose(self) -> ComposeResult:
        options = [(f"{aid} - {name}", aid) for aid, name in CONVERTER_OPTIONS]

        yield Static("Amount:", classes="form-label")
        yield Input(value="100.00", id="amount-input", type="number")

        yield Static("From:", classes="form-label")
        yield Select(options, value="USD", id="from-select", allow_blank=False)

        yield Static("To:", classes="form-label")
        yield Select(options, value="EUR", id="to-select", allow_blank=False)

        with Vertical(classes="result-box"):
            yield Static("Enter values to convert", id="result-line", classes="result-line")
            yield Static("", id="rate-line", classes="rate-line")

    def on_input_changed(self, event: Input.Changed) -> None:
        self._recalculate()

    def on_select_changed(self, event: Select.Changed) -> None:
        self._recalculate()

    def update_prices(self, prices: dict[str, AssetPrice]) -> None:
        self._prices = prices
        self._recalculate()

    def _get_usd_price(self, asset_id: str) -> float | None:
        """Get the USD price for an asset. USD itself is 1.0."""
        if asset_id == "USD":
            return 1.0
        if asset_id in self._prices:
            return self._prices[asset_id].price
        return None

    def _recalculate(self) -> None:
        result = self.query_one("#result-line", Static)
        rate_widget = self.query_one("#rate-line", Static)

        try:
            amount_input = self.query_one("#amount-input", Input)
            from_select = self.query_one("#from-select", Select)
            to_select = self.query_one("#to-select", Select)

            amount = float(amount_input.value) if amount_input.value else 0.0
            from_id = str(from_select.value) if from_select.value else "USD"
            to_id = str(to_select.value) if to_select.value else "EUR"

            from_price = self._get_usd_price(from_id)
            to_price = self._get_usd_price(to_id)

            if from_price is None or to_price is None or to_price == 0:
                result.update("Waiting for price data...")
                rate_widget.update("")
                return

            # Convert: amount in from_currency -> USD -> to_currency
            usd_value = amount * from_price
            converted = usd_value / to_price

            from_name = dict(CONVERTER_OPTIONS).get(from_id, from_id)
            to_name = dict(CONVERTER_OPTIONS).get(to_id, to_id)

            result.update(f"{amount:,.4f} {from_name} = {converted:,.4f} {to_name}")
            rate = from_price / to_price
            rate_widget.update(f"Rate: 1 {from_id} = {rate:.6f} {to_id}")

        except (ValueError, ZeroDivisionError):
            result.update("Invalid input")
            rate_widget.update("")

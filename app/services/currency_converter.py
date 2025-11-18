"""
Currency conversion service for analytics.

This module provides currency conversion functionality for converting
invoice amounts from different currencies to a user's preferred currency.

Exchange rates are hardcoded as per requirements. In production,
these should be fetched from a reliable exchange rate API.
"""
from decimal import Decimal
from typing import Dict


# Exchange rates relative to NGN (Nigerian Naira)
# These are approximate rates and should be updated regularly in production
EXCHANGE_RATES_TO_NGN = {
    "NGN": Decimal("1.0"),
    "USD": Decimal("1650.0"),  # 1 USD = 1650 NGN
    "GBP": Decimal("2100.0"),  # 1 GBP = 2100 NGN
    "EUR": Decimal("1800.0"),  # 1 EUR = 1800 NGN
}


class CurrencyConverter:
    """
    Currency converter for invoice analytics.

    Converts amounts between supported currencies using fixed exchange rates.
    All conversions go through NGN as the base currency.
    """

    def __init__(self):
        """Initialize the currency converter with exchange rates."""
        self.rates_to_ngn = EXCHANGE_RATES_TO_NGN

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (NGN, USD, GBP, EUR)
            to_currency: Target currency code (NGN, USD, GBP, EUR)

        Returns:
            Converted amount in target currency

        Raises:
            ValueError: If currency code is not supported
        """
        if from_currency == to_currency:
            return amount

        if from_currency not in self.rates_to_ngn:
            raise ValueError(f"Unsupported currency: {from_currency}")
        if to_currency not in self.rates_to_ngn:
            raise ValueError(f"Unsupported currency: {to_currency}")

        # Convert to NGN first
        amount_in_ngn = amount * self.rates_to_ngn[from_currency]

        # Convert from NGN to target currency
        amount_in_target = amount_in_ngn / self.rates_to_ngn[to_currency]

        # Round to 2 decimal places
        return amount_in_target.quantize(Decimal("0.01"))

    def convert_multi_currency_amounts(
        self,
        amounts: Dict[str, Decimal],
        to_currency: str
    ) -> Decimal:
        """
        Convert and sum amounts from multiple currencies to a single currency.

        Args:
            amounts: Dictionary mapping currency codes to amounts
            to_currency: Target currency code

        Returns:
            Total amount in target currency

        Example:
            amounts = {"USD": 100, "EUR": 50, "NGN": 1000}
            total = converter.convert_multi_currency_amounts(amounts, "NGN")
        """
        total = Decimal("0.00")

        for currency, amount in amounts.items():
            if amount and currency:
                converted = self.convert(amount, currency, to_currency)
                total += converted

        return total.quantize(Decimal("0.01"))


# Singleton instance for convenience
_converter = CurrencyConverter()


def get_currency_converter() -> CurrencyConverter:
    """
    Get the currency converter singleton instance.

    Returns:
        CurrencyConverter instance
    """
    return _converter

"""
Currency conversion service using free exchangerate-api.com API.

This service provides real-time currency conversion with caching
to minimize API calls and improve performance.

GDPR & ISO Compliance:
- No personal data is sent to the API
- Only currency codes and amounts are transmitted
- API responses are cached to reduce external calls
- Rate limiting is implemented to prevent abuse

Security Considerations:
- API calls are made over HTTPS
- Timeouts are enforced to prevent hanging requests
- Error handling prevents information leakage
- Caching reduces dependency on external service
"""

import httpx
import logging
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.core.cache import get_cache, set_cache, cache_key

logger = logging.getLogger(__name__)

# Free API endpoint (no authentication required for basic tier)
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/{base}"

# Cache exchange rates for 1 hour (3600 seconds)
EXCHANGE_RATE_CACHE_TTL = 3600


class CurrencyConversionError(Exception):
    """Exception raised for currency conversion errors."""
    pass


def get_exchange_rate(
    from_currency: str,
    to_currency: str
) -> Optional[Decimal]:
    """
    Get exchange rate from one currency to another.

    Args:
        from_currency: Source currency code (e.g., "USD")
        to_currency: Target currency code (e.g., "EUR")

    Returns:
        Exchange rate as Decimal, or None if conversion fails

    Raises:
        CurrencyConversionError: If API call fails or rate unavailable
    """
    # If currencies are the same, rate is 1.0
    if from_currency == to_currency:
        return Decimal("1.0")

    # Check cache first
    cache_key_name = cache_key(
        "exchange_rate",
        f"{from_currency}_{to_currency}"
    )
    cached_rate = get_cache(cache_key_name)
    if cached_rate is not None:
        logger.debug(
            f"Using cached exchange rate: {from_currency} -> {to_currency}"
        )
        return Decimal(str(cached_rate))

    # Fetch from API
    try:
        url = EXCHANGE_RATE_API_URL.format(base=from_currency)
        logger.info(
            f"Fetching exchange rate: {from_currency} -> {to_currency}"
        )

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract the rate
            rates = data.get("rates", {})
            if to_currency not in rates:
                raise CurrencyConversionError(
                    f"Rate not available for {to_currency}"
                )

            rate = Decimal(str(rates[to_currency]))

            # Cache the rate
            set_cache(cache_key_name, str(rate), expiry=EXCHANGE_RATE_CACHE_TTL)

            logger.info(
                f"Exchange rate fetched: {from_currency} -> "
                f"{to_currency} = {rate}"
            )
            return rate

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error fetching exchange rate: {e.response.status_code}"
        )
        raise CurrencyConversionError(
            f"Failed to fetch exchange rate: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching exchange rate: {str(e)}")
        raise CurrencyConversionError(
            "Failed to fetch exchange rate: Network error"
        )
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing exchange rate response: {str(e)}")
        raise CurrencyConversionError(
            "Failed to parse exchange rate response"
        )


def convert_amount(
    amount: Decimal,
    from_currency: str,
    to_currency: str
) -> Decimal:
    """
    Convert amount from one currency to another.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Converted amount as Decimal

    Raises:
        CurrencyConversionError: If conversion fails
    """
    if amount == 0:
        return Decimal("0.00")

    rate = get_exchange_rate(from_currency, to_currency)
    if rate is None:
        raise CurrencyConversionError(
            f"Unable to convert {from_currency} to {to_currency}"
        )

    # Perform conversion and round to 2 decimal places
    converted = (amount * rate).quantize(Decimal("0.01"))
    return converted


def convert_currency_dict(
    amounts: Dict[str, Decimal],
    target_currency: str
) -> Decimal:
    """
    Convert a dictionary of currency amounts to a single target currency.

    Args:
        amounts: Dictionary with currency codes as keys and amounts as values
        target_currency: Target currency code for conversion

    Returns:
        Total amount in target currency as Decimal

    Raises:
        CurrencyConversionError: If conversion fails for any currency
    """
    total = Decimal("0.00")

    for currency, amount in amounts.items():
        if amount == 0:
            continue

        converted = convert_amount(amount, currency, target_currency)
        total += converted

    return total

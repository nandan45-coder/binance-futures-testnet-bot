"""
Input validation for Binance Futures Testnet Trading Bot.
All validation logic is centralised here to keep other modules clean.
"""

from __future__ import annotations

import re
from typing import Optional

from bot.logging_config import get_logger

logger = get_logger("validators")

# ── Constants ────────────────────────────────────────────────────────────────

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Binance symbol pattern: uppercase letters + digits, e.g. BTCUSDT, ETHUSDT
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{3,20}$")

MAX_QUANTITY = 1_000_000
MIN_QUANTITY = 0.000001

MAX_PRICE = 10_000_000
MIN_PRICE = 0.000001


# ── Exceptions ───────────────────────────────────────────────────────────────

class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


# ── Validators ───────────────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise a trading symbol.

    Args:
        symbol: Raw symbol string from CLI (e.g. 'btcusdt', 'BTCUSDT').

    Returns:
        Upper-cased, validated symbol.

    Raises:
        ValidationError: If the symbol is invalid.
    """
    if not symbol:
        raise ValidationError("Symbol must not be empty.")

    normalised = symbol.strip().upper()

    if not SYMBOL_PATTERN.match(normalised):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. "
            "Symbols must be 3–20 uppercase letters/digits (e.g. BTCUSDT)."
        )

    logger.debug("Symbol validated: %s", normalised)
    return normalised


def validate_side(side: str) -> str:
    """
    Validate order side.

    Args:
        side: 'BUY' or 'SELL' (case-insensitive).

    Returns:
        Upper-cased side string.

    Raises:
        ValidationError: If the side is not BUY or SELL.
    """
    if not side:
        raise ValidationError("Order side must not be empty.")

    normalised = side.strip().upper()

    if normalised not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )

    logger.debug("Side validated: %s", normalised)
    return normalised


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.

    Args:
        order_type: 'MARKET' or 'LIMIT' (case-insensitive).

    Returns:
        Upper-cased order type string.

    Raises:
        ValidationError: If the order type is not supported.
    """
    if not order_type:
        raise ValidationError("Order type must not be empty.")

    normalised = order_type.strip().upper()

    if normalised not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    logger.debug("Order type validated: %s", normalised)
    return normalised


def validate_quantity(quantity: float | str) -> float:
    """
    Validate order quantity.

    Args:
        quantity: Order quantity (positive float).

    Returns:
        Validated float quantity.

    Raises:
        ValidationError: If the quantity is invalid or out of range.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")

    if qty <= 0:
        raise ValidationError(f"Quantity must be positive, got {qty}.")

    if qty < MIN_QUANTITY:
        raise ValidationError(
            f"Quantity {qty} is below the minimum allowed ({MIN_QUANTITY})."
        )

    if qty > MAX_QUANTITY:
        raise ValidationError(
            f"Quantity {qty} exceeds the maximum allowed ({MAX_QUANTITY})."
        )

    logger.debug("Quantity validated: %s", qty)
    return qty


def validate_price(price: float | str | None, order_type: str) -> Optional[float]:
    """
    Validate order price (required for LIMIT orders, forbidden for MARKET).

    Args:
        price:      Price value from CLI, or None.
        order_type: Already-validated order type ('MARKET' or 'LIMIT').

    Returns:
        Validated float price, or None for MARKET orders.

    Raises:
        ValidationError: If price requirements are not met.
    """
    if order_type == "MARKET":
        if price is not None:
            logger.warning(
                "Price supplied for MARKET order — it will be ignored."
            )
        return None

    # LIMIT order — price is mandatory
    if price is None:
        raise ValidationError("Price is required for LIMIT orders (use --price).")

    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price '{price}' is not a valid number.")

    if p <= 0:
        raise ValidationError(f"Price must be positive, got {p}.")

    if p < MIN_PRICE:
        raise ValidationError(
            f"Price {p} is below the minimum allowed ({MIN_PRICE})."
        )

    if p > MAX_PRICE:
        raise ValidationError(
            f"Price {p} exceeds the maximum allowed ({MAX_PRICE})."
        )

    logger.debug("Price validated: %s", p)
    return p


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
) -> dict:
    """
    Run all validators and return a clean parameter dict.

    Returns:
        dict with keys: symbol, side, order_type, quantity, price
    """
    logger.info("Validating order parameters …")

    validated = {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity":   validate_quantity(quantity),
    }
    validated["price"] = validate_price(price, validated["order_type"])

    logger.info("All parameters passed validation: %s", validated)
    return validated

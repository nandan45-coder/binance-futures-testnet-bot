"""
Order logic for Binance Futures Testnet Trading Bot.
Constructs order parameters and dispatches them via the API client.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient, BinanceAPIError, BinanceAuthError, BinanceNetworkError
from bot.logging_config import get_logger
from bot.validators import validate_all, ValidationError

logger = get_logger("orders")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Build the raw parameter dict for a Binance Futures order.

    Args:
        symbol:        Trading pair (e.g. 'BTCUSDT').
        side:          'BUY' or 'SELL'.
        order_type:    'MARKET' or 'LIMIT'.
        quantity:      Order size.
        price:         Required for LIMIT orders.
        time_in_force: GTC / IOC / FOK (LIMIT only, default GTC).

    Returns:
        Dict ready to pass to client.place_order().
    """
    params: Dict[str, Any] = {
        "symbol":   symbol,
        "side":     side,
        "type":     order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        params["price"] = price
        params["timeInForce"] = time_in_force

    logger.debug("Built order params: %s", params)
    return params


def format_order_summary(order: Dict[str, Any]) -> str:
    """
    Return a human-readable, aligned order summary string.

    Args:
        order: Raw Binance order response dict.

    Returns:
        Formatted multi-line string.
    """
    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║            ORDER PLACED SUCCESSFULLY ✓               ║",
        "╠══════════════════════════════════════════════════════╣",
    ]

    fields = [
        ("Order ID",        order.get("orderId",       "N/A")),
        ("Client Order ID", order.get("clientOrderId", "N/A")),
        ("Symbol",          order.get("symbol",        "N/A")),
        ("Side",            order.get("side",          "N/A")),
        ("Type",            order.get("type",          "N/A")),
        ("Quantity",        order.get("origQty",       order.get("quantity", "N/A"))),
        ("Price",           order.get("price",         "MARKET")),
        ("Status",          order.get("status",        "N/A")),
        ("Time in Force",   order.get("timeInForce",   "N/A")),
        ("Avg Fill Price",  order.get("avgPrice",      "N/A")),
        ("Executed Qty",    order.get("executedQty",   "N/A")),
        ("Timestamp",       order.get("updateTime",    "N/A")),
    ]

    for label, value in fields:
        line = f"║  {label:<18} : {str(value):<31}║"
        lines.append(line)

    lines.append("╚══════════════════════════════════════════════════════╝")
    lines.append("")

    return "\n".join(lines)


# ── Main order function ───────────────────────────────────────────────────────

def place_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: Optional[float | str] = None,
    client: Optional[BinanceFuturesClient] = None,
) -> Dict[str, Any]:
    """
    Validate inputs, build parameters, and place an order on Binance Futures Testnet.

    Args:
        symbol:     Trading pair symbol.
        side:       BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity:   Order quantity.
        price:      Required for LIMIT orders.
        client:     Optional pre-built BinanceFuturesClient (created if None).

    Returns:
        Raw Binance API response dict.

    Raises:
        ValidationError:    On invalid user inputs.
        BinanceAuthError:   On authentication failures.
        BinanceAPIError:    On Binance API errors.
        BinanceNetworkError: On network-level failures.
    """
    # Validate all inputs
    try:
        validated = validate_all(symbol, side, order_type, quantity, price)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        raise

    # Create client if not provided
    if client is None:
        client = BinanceFuturesClient()

    # Build order parameters
    params = _build_order_params(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated["price"],
    )

    logger.info(
        "Placing %s %s order | symbol=%s | qty=%s | price=%s",
        validated["side"],
        validated["order_type"],
        validated["symbol"],
        validated["quantity"],
        validated["price"] or "MARKET",
    )

    try:
        response = client.place_order(params)
    except BinanceAuthError as exc:
        logger.error("Authentication error: %s", exc)
        raise
    except BinanceAPIError as exc:
        logger.error("Binance API error [%s]: %s", exc.code, exc.message)
        raise
    except BinanceNetworkError as exc:
        logger.error("Network error: %s", exc)
        raise

    logger.info("Order placed successfully: orderId=%s", response.get("orderId"))
    return response

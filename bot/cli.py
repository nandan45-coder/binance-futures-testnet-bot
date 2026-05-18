"""
CLI entry point for the Binance Futures Testnet Trading Bot.
Built with Click — supports MARKET and LIMIT orders with full validation.

Usage examples:
    python -m bot.cli place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.001
    python -m bot.cli place-order --symbol ETHUSDT --side SELL --order-type LIMIT --quantity 0.1 --price 3000
    python -m bot.cli account-info
    python -m bot.cli server-time
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
from dotenv import load_dotenv

from bot.client import (
    BinanceAPIError,
    BinanceAuthError,
    BinanceFuturesClient,
    BinanceNetworkError,
)
from bot.logging_config import setup_logger
from bot.orders import format_order_summary, place_order
from bot.validators import ValidationError

load_dotenv()

# Initialise root logger once at startup
logger = setup_logger("trading_bot")


# ── CLI group ────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="Binance Futures Testnet Bot")
def cli() -> None:
    """
    \b
    ╔══════════════════════════════════════════════════╗
    ║   Binance Futures Testnet Trading Bot  v1.0.0   ║
    ║   USDT-M Perpetual Futures · Testnet Only       ║
    ╚══════════════════════════════════════════════════╝

    Place MARKET and LIMIT orders on Binance Futures Testnet.
    Credentials are read from the .env file or environment variables.
    """


# ── place-order command ───────────────────────────────────────────────────────

@cli.command("place-order")
@click.option(
    "--symbol",
    required=True,
    metavar="SYMBOL",
    help="Trading pair symbol, e.g. BTCUSDT",
)
@click.option(
    "--side",
    required=True,
    type=click.Choice(["BUY", "SELL"], case_sensitive=False),
    help="Order side: BUY or SELL",
)
@click.option(
    "--order-type",
    "order_type",
    required=True,
    type=click.Choice(["MARKET", "LIMIT"], case_sensitive=False),
    help="Order type: MARKET or LIMIT",
)
@click.option(
    "--quantity",
    required=True,
    type=float,
    metavar="QTY",
    help="Order quantity (positive float)",
)
@click.option(
    "--price",
    default=None,
    type=float,
    metavar="PRICE",
    help="Limit price (required for LIMIT orders)",
)
@click.option(
    "--json-output",
    "json_output",
    is_flag=True,
    default=False,
    help="Print raw JSON response instead of formatted summary",
)
def place_order_cmd(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    json_output: bool,
) -> None:
    """Place a MARKET or LIMIT futures order on the Binance Testnet."""

    click.echo(f"\n🔄  Placing {side.upper()} {order_type.upper()} order for {symbol.upper()} …\n")

    try:
        response = place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValidationError as exc:
        click.secho(f"\n❌  Validation Error: {exc}\n", fg="red", err=True)
        logger.error("Validation error: %s", exc)
        sys.exit(1)
    except BinanceAuthError as exc:
        click.secho(
            f"\n🔑  Authentication Error [{exc.code}]: {exc.message}\n"
            "    → Check BINANCE_API_KEY and BINANCE_SECRET_KEY in your .env file.\n",
            fg="red",
            err=True,
        )
        sys.exit(1)
    except BinanceAPIError as exc:
        click.secho(f"\n⚠️   Binance API Error [{exc.code}]: {exc.message}\n", fg="yellow", err=True)
        sys.exit(1)
    except BinanceNetworkError as exc:
        click.secho(f"\n🌐  Network Error: {exc}\n", fg="red", err=True)
        sys.exit(1)
    except Exception as exc:
        click.secho(f"\n💥  Unexpected Error: {exc}\n", fg="red", err=True)
        logger.exception("Unexpected error during order placement")
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(response, indent=2))
    else:
        click.secho(format_order_summary(response), fg="green")

    logger.info("Order command completed successfully.")


# ── account-info command ─────────────────────────────────────────────────────

@cli.command("account-info")
@click.option(
    "--json-output",
    "json_output",
    is_flag=True,
    default=False,
    help="Print raw JSON response",
)
def account_info_cmd(json_output: bool) -> None:
    """Fetch and display Binance Futures Testnet account information."""

    click.echo("\n🔍  Fetching account information …\n")

    try:
        client = BinanceFuturesClient()
        info = client.get_account_info()
    except BinanceAuthError as exc:
        click.secho(f"\n🔑  Authentication Error [{exc.code}]: {exc.message}\n", fg="red", err=True)
        sys.exit(1)
    except (BinanceAPIError, BinanceNetworkError) as exc:
        click.secho(f"\n⚠️   Error: {exc}\n", fg="yellow", err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(info, indent=2))
        return

    # Pretty-print selected fields
    click.secho("╔══════════════════════════════════════╗", fg="cyan")
    click.secho("║       ACCOUNT INFORMATION            ║", fg="cyan")
    click.secho("╠══════════════════════════════════════╣", fg="cyan")
    click.secho(f"║  Total Balance   : {info.get('totalWalletBalance', 'N/A'):<18}║", fg="cyan")
    click.secho(f"║  Available Bal.  : {info.get('availableBalance', 'N/A'):<18}║", fg="cyan")
    click.secho(f"║  Unrealised PnL  : {info.get('totalUnrealizedProfit', 'N/A'):<18}║", fg="cyan")
    click.secho(f"║  Total Margin    : {info.get('totalInitialMargin', 'N/A'):<18}║", fg="cyan")
    click.secho(f"║  Can Trade       : {str(info.get('canTrade', 'N/A')):<18}║", fg="cyan")
    click.secho("╚══════════════════════════════════════╝\n", fg="cyan")


# ── server-time command ───────────────────────────────────────────────────────

@cli.command("server-time")
def server_time_cmd() -> None:
    """Fetch Binance Futures Testnet server time (connectivity check)."""

    try:
        client = BinanceFuturesClient()
        result = client.get_server_time()
        ts = result.get("serverTime", "N/A")
        click.secho(f"\n✅  Server Time: {ts} (ms since epoch)\n", fg="green")
    except BinanceAuthError as exc:
        click.secho(f"\n🔑  Authentication Error: {exc.message}\n", fg="red", err=True)
        sys.exit(1)
    except (BinanceAPIError, BinanceNetworkError) as exc:
        click.secho(f"\n⚠️   Error: {exc}\n", fg="yellow", err=True)
        sys.exit(1)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()

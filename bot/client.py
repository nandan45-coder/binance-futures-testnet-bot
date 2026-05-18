"""
Binance Futures Testnet API client wrapper.
Handles authentication (HMAC-SHA256), request signing, and HTTP communication.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from bot.logging_config import get_logger

load_dotenv()

logger = get_logger("client")

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
RECV_WINDOW = 5000    # ms


# ── Exceptions ───────────────────────────────────────────────────────────────

class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error [{code}]: {message}")


class BinanceAuthError(BinanceAPIError):
    """Raised for authentication / key-related API errors."""


class BinanceNetworkError(Exception):
    """Raised when a network-level failure occurs."""


# ── Client ───────────────────────────────────────────────────────────────────

class BinanceFuturesClient:
    """
    Minimal, production-grade Binance Futures Testnet REST client.

    Reads credentials from environment variables:
        BINANCE_API_KEY
        BINANCE_SECRET_KEY
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.secret_key = secret_key or os.getenv("BINANCE_SECRET_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        if not self.api_key or not self.secret_key:
            raise BinanceAuthError(
                -1000,
                "BINANCE_API_KEY and BINANCE_SECRET_KEY must be set "
                "(check your .env file or environment variables).",
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        logger.info("BinanceFuturesClient initialised (base_url=%s)", self.base_url)

    # ── Signature helpers ────────────────────────────────────────────────────

    def _timestamp(self) -> int:
        """Return current UTC timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for a parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        logger.debug("Signature generated for params: %s", list(params.keys()))
        return signature

    # ── HTTP helpers ─────────────────────────────────────────────────────────

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse response, raise structured exceptions on error."""
        logger.debug(
            "Response [%s] from %s: %s",
            response.status_code,
            response.url,
            response.text[:500],
        )

        try:
            data = response.json()
        except ValueError:
            raise BinanceNetworkError(
                f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}"
            )

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            code = data["code"]
            msg = data.get("msg", "Unknown error")

            # Authentication errors
            if code in (-2014, -2015, -1022, -2008):
                raise BinanceAuthError(code, msg)

            raise BinanceAPIError(code, msg)

        return data

    def _get(self, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Any:
        """Send a signed or unsigned GET request."""
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = RECV_WINDOW
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        logger.info("GET %s | params: %s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self._session.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.ConnectionError as exc:
            raise BinanceNetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.Timeout:
            raise BinanceNetworkError(f"Request timed out after {self.timeout}s.")
        except requests.exceptions.RequestException as exc:
            raise BinanceNetworkError(f"Request error: {exc}") from exc

        return self._handle_response(response)

    def _post(self, endpoint: str, params: Optional[Dict] = None, signed: bool = True) -> Any:
        """Send a signed POST request."""
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = RECV_WINDOW
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        logger.info("POST %s | params: %s", url, safe_params)

        try:
            response = self._session.post(url, data=params, timeout=self.timeout)
        except requests.exceptions.ConnectionError as exc:
            raise BinanceNetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.Timeout:
            raise BinanceNetworkError(f"Request timed out after {self.timeout}s.")
        except requests.exceptions.RequestException as exc:
            raise BinanceNetworkError(f"Request error: {exc}") from exc

        return self._handle_response(response)

    # ── Public API methods ───────────────────────────────────────────────────

    def get_server_time(self) -> Dict[str, Any]:
        """Fetch server time (no auth required — useful for connectivity check)."""
        return self._get("/fapi/v1/time")

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange info (symbols, filters, etc.)."""
        return self._get("/fapi/v1/exchangeInfo")

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account information (signed)."""
        return self._get("/fapi/v2/account", signed=True)

    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a futures order.

        Args:
            params: Order parameters (symbol, side, type, quantity, price, etc.)

        Returns:
            Binance order response dict.
        """
        return self._post("/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Query a specific order by ID."""
        return self._get(
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order."""
        params = {"symbol": symbol, "orderId": order_id}
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)

        url = f"{self.base_url}/fapi/v1/order"
        logger.info("DELETE %s | orderId=%s", url, order_id)

        try:
            response = self._session.delete(url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise BinanceNetworkError(f"Request error: {exc}") from exc

        return self._handle_response(response)

"""
Binance Futures Testnet REST client.
Handles authentication (HMAC-SHA256), request signing, and raw HTTP calls.
"""

import hashlib
import hmac
import time
import logging
import json
from urllib.parse import urlencode

import requests

BASE_URL = "https://testnet.binancefuture.com"
logger = logging.getLogger("trading_bot.client")


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"Binance API error {code}: {msg}")


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.debug("BinanceClient initialised (base URL: %s)", BASE_URL)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append a HMAC-SHA256 signature to params."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _handle_response(self, response: requests.Response) -> dict:
        """Parse the response and raise on API-level errors."""
        logger.debug("HTTP %s %s", response.status_code, response.url)
        try:
            data = response.json()
        except Exception:
            response.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            # Binance error envelope: {"code": -1121, "msg": "..."}
            if data["code"] < 0:
                logger.error("API error response: %s", json.dumps(data))
                raise BinanceClientError(data["code"], data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API (no signature needed)
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Test connectivity."""
        try:
            r = self._session.get(f"{BASE_URL}/fapi/v1/ping", timeout=self._timeout)
            r.raise_for_status()
            logger.info("Ping successful — testnet is reachable.")
            return True
        except requests.RequestException as exc:
            logger.error("Ping failed: %s", exc)
            return False

    def get_exchange_info(self, symbol: str) -> dict:
        """Fetch symbol metadata (filters, precision, etc.)."""
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        logger.debug("GET exchangeInfo for %s", symbol)
        r = self._session.get(url, params={"symbol": symbol}, timeout=self._timeout)
        return self._handle_response(r)

    # ------------------------------------------------------------------
    # Private / signed endpoints
    # ------------------------------------------------------------------

    def get_account(self) -> dict:
        """Return account info (balances, positions)."""
        params = self._sign({"timestamp": self._timestamp()})
        url = f"{BASE_URL}/fapi/v2/account"
        logger.debug("GET account")
        r = self._session.get(url, params=params, timeout=self._timeout)
        return self._handle_response(r)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a futures order.

        Parameters
        ----------
        symbol       : e.g. 'BTCUSDT'
        side         : 'BUY' | 'SELL'
        order_type   : 'MARKET' | 'LIMIT' | 'STOP_MARKET'
        quantity     : order size in base asset
        price        : required for LIMIT
        stop_price   : required for STOP_MARKET
        time_in_force: 'GTC' | 'IOC' | 'FOK' (LIMIT only)
        reduce_only  : only reduce an existing position
        """
        params: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": self._timestamp(),
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )
        logger.debug("Order params (pre-sign): %s", json.dumps(params, default=str))

        signed = self._sign(params)
        url = f"{BASE_URL}/fapi/v1/order"

        try:
            r = self._session.post(url, data=signed, timeout=self._timeout)
        except requests.ConnectionError as exc:
            logger.error("Network error while placing order: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request timed out while placing order.")
            raise

        result = self._handle_response(r)
        logger.info("Order response: %s", json.dumps(result, default=str))
        return result

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query the status of an existing order."""
        params = self._sign({
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": self._timestamp(),
        })
        url = f"{BASE_URL}/fapi/v1/order"
        r = self._session.get(url, params=params, timeout=self._timeout)
        return self._handle_response(r)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order."""
        params = self._sign({
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": self._timestamp(),
        })
        url = f"{BASE_URL}/fapi/v1/order"
        r = self._session.delete(url, params=params, timeout=self._timeout)
        return self._handle_response(r)

"""
bot — Binance Futures Testnet trading bot package.

Modules:
    client.py       — low-level Binance REST client (auth, signing, HTTP)
    orders.py       — order placement logic and response formatting
    validators.py   — input validation for all order parameters
    logging_config  — structured logging to file + console
"""

from bot.client import BinanceClient, BinanceClientError
from bot.orders import place_order
from bot.validators import ValidationError

__all__ = ["BinanceClient", "BinanceClientError", "place_order", "ValidationError"]
__version__ = "1.0.0"

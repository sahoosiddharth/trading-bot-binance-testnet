"""Input validation logic for order parameters."""

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(f"Symbol '{symbol}' must be alphanumeric (e.g. BTCUSDT).")
    return symbol


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {VALID_SIDES}. Got: '{side}'")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(f"Order type must be one of {VALID_ORDER_TYPES}. Got: '{order_type}'")
    return order_type


def validate_quantity(quantity: str) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a positive number. Got: '{quantity}'")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero. Got: {qty}")
    return qty


def validate_price(price: str) -> float:
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price must be a positive number. Got: '{price}'")
    if p <= 0:
        raise ValidationError(f"Price must be greater than zero. Got: {p}")
    return p


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str = None,
    stop_price: str = None,
) -> dict:
    """
    Validate all order parameters together and return a clean dict.
    Raises ValidationError on any problem.
    """
    params = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }

    if params["order_type"] == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        params["price"] = validate_price(price)

    if params["order_type"] == "STOP_MARKET":
        if stop_price is None:
            raise ValidationError("Stop price is required for STOP_MARKET orders.")
        params["stop_price"] = validate_price(stop_price)

    return params

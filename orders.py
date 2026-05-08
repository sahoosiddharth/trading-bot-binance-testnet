"""
Order placement logic — sits between the CLI and the raw HTTP client.
Formats results using rich for beautiful terminal output.
"""

import logging
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

from bot.client import BinanceClient, BinanceClientError
from bot.validators import validate_order_params, ValidationError

logger = logging.getLogger("trading_bot.orders")
console = Console()


def _print_request_summary(params: dict):
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", min_width=44)
    table.add_column("Field", style="cyan", width=14)
    table.add_column("Value", style="bold white")

    table.add_row("Symbol",    params["symbol"])
    table.add_row("Side",      f"[green]{params['side']}[/green]" if params["side"] == "BUY" else f"[red]{params['side']}[/red]")
    table.add_row("Type",      params["order_type"])
    table.add_row("Quantity",  str(params["quantity"]))
    if "price" in params:
        table.add_row("Price", str(params["price"]))
    if "stop_price" in params:
        table.add_row("Stop Price", str(params["stop_price"]))

    console.print(Panel(table, title="[bold cyan]ORDER REQUEST[/bold cyan]", border_style="cyan"))


def _print_response(data: dict):
    status = data.get("status", "UNKNOWN")
    status_color = {
        "FILLED": "green",
        "NEW": "yellow",
        "PARTIALLY_FILLED": "yellow",
        "CANCELED": "red",
    }.get(status, "white")

    table = Table(box=box.ROUNDED, show_header=False, border_style="green", min_width=44)
    table.add_column("Field", style="cyan", width=14)
    table.add_column("Value", style="bold white")

    table.add_row("Order ID",   str(data.get("orderId", "N/A")))
    table.add_row("Symbol",     data.get("symbol", "N/A"))
    table.add_row("Side",       data.get("side", "N/A"))
    table.add_row("Type",       data.get("type", "N/A"))
    table.add_row("Status",     f"[{status_color}]{status}[/{status_color}]")
    table.add_row("Quantity",   data.get("origQty", "N/A"))
    table.add_row("Exec Qty",   data.get("executedQty", "N/A"))
    table.add_row("Avg Price",  data.get("avgPrice", "N/A"))
    table.add_row("Price",      data.get("price", "N/A"))
    table.add_row("Stop Price", data.get("stopPrice", "N/A"))
    table.add_row("Timestamp",  str(data.get("updateTime", "N/A")))

    console.print(Panel(table, title="[bold green]ORDER RESPONSE[/bold green]", border_style="green"))

    if status in ("FILLED", "NEW", "PARTIALLY_FILLED"):
        console.print(f"  [bold green]✓ Order placed successfully (status: {status})[/bold green]\n")
    else:
        console.print(f"  [bold yellow]⚠ Order status: {status}[/bold yellow]\n")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """Validate inputs, place the order, print rich output, return response."""

    try:
        params = validate_order_params(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=price, stop_price=stop_price,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        console.print(f"\n[bold red]✗ Validation Error:[/bold red] {exc}\n")
        raise

    _print_request_summary(params)

    try:
        response = client.place_order(
            symbol=params["symbol"], side=params["side"],
            order_type=params["order_type"], quantity=params["quantity"],
            price=params.get("price"), stop_price=params.get("stop_price"),
        )
    except BinanceClientError as exc:
        logger.error("Order failed with API error: %s", exc)
        console.print(f"\n[bold red]✗ ORDER FAILED:[/bold red] {exc}\n")
        raise
    except Exception as exc:
        logger.error("Unexpected error placing order: %s", exc)
        console.print(f"\n[bold red]✗ Unexpected error:[/bold red] {exc}\n")
        raise

    _print_response(response)
    return response

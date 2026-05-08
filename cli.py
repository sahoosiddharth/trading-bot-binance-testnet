#!/usr/bin/env python3
"""
Binance Futures Testnet — Trading Bot CLI
Usage examples are in README.md
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import ValidationError

load_dotenv()
console = Console()


def get_credentials() -> tuple[str, str]:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        console.print("\n[bold red]ERROR:[/bold red] BINANCE_API_KEY and BINANCE_API_SECRET must be set.\n")
        console.print("  [cyan]Option 1[/cyan] — export them:")
        console.print("    export BINANCE_API_KEY=your_key")
        console.print("    export BINANCE_API_SECRET=your_secret\n")
        console.print("  [cyan]Option 2[/cyan] — create a [bold].env[/bold] file:")
        console.print("    BINANCE_API_KEY=your_key")
        console.print("    BINANCE_API_SECRET=your_secret\n")
        sys.exit(1)
    return api_key, api_secret


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet order placer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python cli.py --ping
  python cli.py --account
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET     --quantity 0.001
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT       --quantity 0.001 --price 70000
  python cli.py --symbol BTCUSDT --side BUY  --type STOP_MARKET --quantity 0.001 --stop-price 60000
        """,
    )
    parser.add_argument("--symbol",     type=str)
    parser.add_argument("--side",       type=str, choices=["BUY", "SELL"])
    parser.add_argument("--type",       dest="order_type", type=str,
                        choices=["MARKET", "LIMIT", "STOP_MARKET"])
    parser.add_argument("--quantity",   type=str)
    parser.add_argument("--price",      type=str, default=None)
    parser.add_argument("--stop-price", type=str, default=None, dest="stop_price")
    parser.add_argument("--ping",       action="store_true", help="Ping testnet and exit")
    parser.add_argument("--account",    action="store_true", help="Show account balances and exit")
    return parser


def cmd_ping(client: BinanceClient):
    ok = client.ping()
    if ok:
        console.print("[bold green]✓ Testnet reachable[/bold green]")
    else:
        console.print("[bold red]✗ Testnet unreachable[/bold red]")
    sys.exit(0 if ok else 1)


def cmd_account(client: BinanceClient):
    data = client.get_account()
    assets = [a for a in data.get("assets", []) if float(a.get("walletBalance", 0)) != 0]

    table = Table(box=box.ROUNDED, border_style="cyan", title="[bold cyan]Account Balances[/bold cyan]")
    table.add_column("Asset",          style="cyan",  min_width=8)
    table.add_column("Wallet Balance", style="white", min_width=18)
    table.add_column("Unrealised PnL", style="white", min_width=18)

    for a in assets:
        pnl = float(a.get("unrealizedProfit", 0))
        pnl_str = f"[green]+{pnl}[/green]" if pnl >= 0 else f"[red]{pnl}[/red]"
        table.add_row(a["asset"], a["walletBalance"], pnl_str)

    if not assets:
        console.print("[yellow]No funded assets found — use the testnet faucet first.[/yellow]")
    else:
        console.print(table)
    sys.exit(0)


def main():
    logger = setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    api_key, api_secret = get_credentials()
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    if args.ping:
        cmd_ping(client)

    if args.account:
        cmd_account(client)

    required_for_order = ["symbol", "side", "order_type", "quantity"]
    missing = [f"--{f.replace('_', '-')}" for f in required_for_order if not getattr(args, f, None)]
    if missing:
        parser.error(f"The following arguments are required to place an order: {', '.join(missing)}")

    try:
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        console.print(f"\n[bold red]Validation Error:[/bold red] {exc}\n")
        sys.exit(1)
    except BinanceClientError as exc:
        console.print(f"\n[bold red]API Error [{exc.code}]:[/bold red] {exc.msg}\n")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unhandled exception")
        console.print(f"\n[bold red]Unexpected error:[/bold red] {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

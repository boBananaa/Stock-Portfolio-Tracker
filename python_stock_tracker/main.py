"""Command-line interface for the portfolio tracker."""

from __future__ import annotations

import argparse
import math
import sys

from portfolio import (
    add_stock,
    load_portfolio,
    refresh_prices,
    remove_stock,
    update_shares,
)


def print_portfolio() -> None:
    """Print holdings, their market values, and their portfolio percentages."""
    holdings = load_portfolio()
    market_values = [
        value
        for holding in holdings
        if (value := holding.market_value) is not None
    ]
    total_value = sum(market_values)

    if not holdings:
        print("Your portfolio is empty.")
        return

    print(
        f"{'Ticker':<8} {'Shares':>10} {'Price':>12} "
        f"{'Value':>14} {'Portfolio':>12}"
    )
    print("-" * 62)

    for holding in holdings:
        price = (
            f"${holding.current_price:,.2f}"
            if holding.current_price is not None
            else "Unavailable"
        )
        market_value = holding.market_value
        value = (
            f"${market_value:,.2f}"
            if market_value is not None
            else "Unavailable"
        )
        percentage = (
            f"{market_value / total_value:.1%}"
            if market_value is not None and total_value > 0
            else "Unavailable"
        )
        print(
            f"{holding.ticker:<8} {holding.shares:>10.2f} {price:>12} "
            f"{value:>14} {percentage:>12}"
        )

    print("-" * 62)
    print(f"Total market value: ${total_value:,.2f}")


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line options without performing any portfolio work."""
    parser = argparse.ArgumentParser(description="Manage and view a stock portfolio.")
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("view", help="Print holdings, values, and portfolio percentages.")
    commands.add_parser("refresh", help="Get latest prices from Yahoo Finance.")

    add_parser = commands.add_parser("add", help="Add a stock to the portfolio.")
    add_parser.add_argument("ticker", help="Ticker symbol, for example AAPL")
    add_parser.add_argument("shares", type=float, help="Number of shares owned")
    add_parser.add_argument("average_cost", type=float, help="Average price paid per share")

    remove_parser = commands.add_parser("remove", help="Remove a stock from the portfolio.")
    remove_parser.add_argument("ticker", help="Ticker symbol to remove")

    shares_parser = commands.add_parser("shares", help="Set the total shares owned for a stock.")
    shares_parser.add_argument("ticker", help="Ticker symbol to update")
    shares_parser.add_argument("shares", type=float, help="New total number of shares owned")

    chart_parser = commands.add_parser("chart", help="Show a portfolio allocation donut chart.")
    chart_parser.add_argument(
        "--start-color",
        default="#4F46E5",
        help="First gradient color as a hex value (default: #4F46E5)",
    )
    chart_parser.add_argument(
        "--end-color",
        default="#22C55E",
        help="Last gradient color as a hex value (default: #22C55E)",
    )
    chart_parser.add_argument("--save", help="Optional PNG output path instead of opening a window")
    return parser


def show_chart(
    start_color: str = "#4F46E5",
    end_color: str = "#22C55E",
    save_path: str | None = None,
) -> None:
    """Open or save the chart without making the rest of the app import Matplotlib."""
    from portfolio_chart import show_portfolio_chart

    show_portfolio_chart(start_color, end_color, save_path)


def run_command(args: argparse.Namespace) -> None:
    """Run one action selected through either the menu or command line."""

    if args.command == "view":
        print_portfolio()
    elif args.command == "refresh":
        refresh_prices()
    elif args.command == "add":
        add_stock(args.ticker, args.shares, args.average_cost)
        print(f"Added {args.ticker.upper()}. Run refresh to fetch its current price.")
    elif args.command == "remove":
        remove_stock(args.ticker)
        print(f"Removed {args.ticker.upper()}.")
    elif args.command == "shares":
        update_shares(args.ticker, args.shares)
        print(f"Updated {args.ticker.upper()} to {args.shares:g} shares.")
    elif args.command == "chart":
        show_chart(args.start_color, args.end_color, args.save)


def prompt_number(message: str) -> float:
    """Keep asking until the user enters a valid decimal number."""
    while True:
        try:
            value = float(input(message).strip())
            if not math.isfinite(value):
                raise ValueError
            return value
        except ValueError:
            print("Please enter a finite number, for example: 2 or 120.50")


def interactive_menu() -> None:
    """Let a user manage the portfolio without typing command-line arguments."""
    while True:
        print("\nPortfolio Tracker")
        print("1. View portfolio")
        print("2. Refresh current prices")
        print("3. Add a stock")
        print("4. Remove a stock")
        print("5. Update shares")
        print("6. Show or save donut chart")
        print("0. Quit")

        try:
            choice = input("Choose an option: ").strip()
        except EOFError:
            print("\nGoodbye.")
            return

        try:
            if choice == "0":
                print("Goodbye.")
                return
            if choice == "1":
                print_portfolio()
            elif choice == "2":
                refresh_prices()
            elif choice == "3":
                ticker = input("Ticker symbol: ").strip()
                shares = prompt_number("Number of shares: ")
                average_cost = prompt_number("Average cost per share: $")
                add_stock(ticker, shares, average_cost)
                print(f"Added {ticker.upper()}.")
            elif choice == "4":
                ticker = input("Ticker symbol to remove: ").strip()
                remove_stock(ticker)
                print(f"Removed {ticker.upper()}.")
            elif choice == "5":
                ticker = input("Ticker symbol to update: ").strip()
                shares = prompt_number("New total number of shares: ")
                update_shares(ticker, shares)
                print(f"Updated {ticker.upper()} to {shares:g} shares.")
            elif choice == "6":
                start_color = input("Start hex color [#4F46E5]: ").strip() or "#4F46E5"
                end_color = input("End hex color [#22C55E]: ").strip() or "#22C55E"
                save_path = input("PNG filename (leave blank to open): ").strip() or None
                show_chart(start_color, end_color, save_path)
            else:
                print("Please choose a number from 0 to 6.")
        except (OSError, ValueError) as error:
            print(f"Could not complete that action: {error}")


def main() -> None:
    """Start the interactive menu or run a command-line action."""
    if len(sys.argv) == 1:
        interactive_menu()
        return

    parser = build_parser()
    args = parser.parse_args()
    try:
        run_command(args)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()

"""Portfolio CSV storage and Yahoo Finance price services."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import yfinance as yf


PORTFOLIO_FILE = Path(__file__).with_name("portfolio.csv")
FIELDNAMES = ["ticker", "shares", "average_cost", "current_price"]


@dataclass(frozen=True)
class Holding:
    """One position from portfolio.csv."""

    ticker: str
    shares: float
    average_cost: float
    current_price: float | None

    @property
    def market_value(self) -> float | None:
        """Return shares times current price when a price is available."""
        if self.current_price is None:
            return None
        return self.shares * self.current_price


def _to_price(value: str | None) -> float | None:
    """Convert a CSV price to a float; blank and null values mean no price yet."""
    if value is None or value.strip().lower() in {"", "null", "none"}:
        return None
    return float(value)


def _validated_holding(
    ticker: str,
    shares: float,
    average_cost: float,
    current_price: float | None,
    *,
    context: str,
) -> Holding:
    """Normalize and validate one holding before it enters the portfolio."""
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise ValueError(f"{context}: ticker cannot be empty")

    numeric_values = {
        "shares": shares,
        "average_cost": average_cost,
    }
    if current_price is not None:
        numeric_values["current_price"] = current_price

    for name, value in numeric_values.items():
        if not math.isfinite(value):
            raise ValueError(f"{context}: {name} must be a finite number")

    if shares <= 0:
        raise ValueError(f"{context}: shares must be greater than zero")
    if average_cost < 0:
        raise ValueError(f"{context}: average_cost cannot be negative")
    if current_price is not None and current_price <= 0:
        raise ValueError(f"{context}: current_price must be greater than zero")

    return Holding(normalized_ticker, shares, average_cost, current_price)


def _ensure_portfolio_file() -> None:
    """Create an empty, valid portfolio CSV on the first run."""
    if PORTFOLIO_FILE.exists():
        return

    with PORTFOLIO_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()


def load_portfolio() -> list[Holding]:
    """Load and validate the portfolio CSV into reusable Holding objects."""
    _ensure_portfolio_file()
    with PORTFOLIO_FILE.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        fieldnames = [name.strip() for name in reader.fieldnames or []]
        if fieldnames != FIELDNAMES:
            raise ValueError(f"portfolio.csv headers must be: {', '.join(FIELDNAMES)}")
        reader.fieldnames = fieldnames

        holdings: list[Holding] = []
        seen_tickers: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"portfolio.csv row {row_number} has too many columns")
            if all(not (value or "").strip() for value in row.values()):
                continue

            try:
                holding = _validated_holding(
                    ticker=row["ticker"],
                    shares=float(row["shares"]),
                    average_cost=float(row["average_cost"]),
                    current_price=_to_price(row["current_price"]),
                    context=f"portfolio.csv row {row_number}",
                )
            except (KeyError, TypeError, ValueError) as error:
                if isinstance(error, ValueError) and str(error).startswith("portfolio.csv row"):
                    raise
                raise ValueError(f"portfolio.csv row {row_number} contains invalid data") from error

            if holding.ticker in seen_tickers:
                raise ValueError(f"portfolio.csv contains duplicate ticker {holding.ticker}")
            seen_tickers.add(holding.ticker)
            holdings.append(holding)

        return holdings


def save_portfolio(holdings: list[Holding]) -> None:
    """Validate and atomically persist holdings in the shared CSV format."""
    validated: list[Holding] = []
    seen_tickers: set[str] = set()
    for index, holding in enumerate(holdings, start=1):
        clean_holding = _validated_holding(
            holding.ticker,
            holding.shares,
            holding.average_cost,
            holding.current_price,
            context=f"holding {index}",
        )
        if clean_holding.ticker in seen_tickers:
            raise ValueError(f"portfolio contains duplicate ticker {clean_holding.ticker}")
        seen_tickers.add(clean_holding.ticker)
        validated.append(clean_holding)

    temporary_file = PORTFOLIO_FILE.with_name(f".{PORTFOLIO_FILE.name}.tmp")
    try:
        with temporary_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            for holding in validated:
                writer.writerow(
                    {
                        "ticker": holding.ticker,
                        "shares": f"{holding.shares:g}",
                        "average_cost": f"{holding.average_cost:.2f}",
                        "current_price": (
                            f"{holding.current_price:.2f}"
                            if holding.current_price is not None
                            else "null"
                        ),
                    }
                )
        temporary_file.replace(PORTFOLIO_FILE)
    finally:
        temporary_file.unlink(missing_ok=True)


def get_current_price(ticker_symbol: str) -> float:
    """Fetch the latest available Yahoo Finance price for one ticker."""
    ticker_symbol = ticker_symbol.strip().upper()
    if not ticker_symbol:
        raise ValueError("Ticker cannot be empty")

    ticker = yf.Ticker(ticker_symbol)
    price = None
    try:
        price = ticker.fast_info.get("last_price")
    except Exception:
        # Yahoo occasionally does not provide fast_info for a valid symbol.
        pass

    if price is None:
        price = ticker.info.get("regularMarketPrice")
    if price is None:
        raise ValueError(f"No current market price was returned for {ticker_symbol}")

    numeric_price = float(price)
    if not math.isfinite(numeric_price) or numeric_price <= 0:
        raise ValueError(f"Yahoo Finance returned an invalid price for {ticker_symbol}")
    return numeric_price


def refresh_prices() -> None:
    """Fetch and save current prices, retaining the old price after a failure."""
    holdings = load_portfolio()
    if not holdings:
        print("Your portfolio is empty. Add a stock before refreshing prices.")
        return

    refreshed: list[Holding] = []
    for holding in holdings:
        try:
            price = get_current_price(holding.ticker)
            refreshed.append(Holding(holding.ticker, holding.shares, holding.average_cost, price))
            print(f"Updated {holding.ticker}: ${price:.2f}")
        except Exception as error:
            refreshed.append(holding)
            print(f"Could not update {holding.ticker}: {error}")
    save_portfolio(refreshed)


def add_stock(ticker: str, shares: float, average_cost: float) -> None:
    """Add a unique stock position. Refresh afterward to fetch its price."""
    new_holding = _validated_holding(
        ticker,
        shares,
        average_cost,
        None,
        context="new holding",
    )

    holdings = load_portfolio()
    if any(holding.ticker == new_holding.ticker for holding in holdings):
        raise ValueError(f"{new_holding.ticker} is already in portfolio.csv")

    save_portfolio([*holdings, new_holding])


def remove_stock(ticker: str) -> None:
    """Remove an existing stock position by ticker symbol."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker cannot be empty")
    holdings = load_portfolio()
    remaining = [holding for holding in holdings if holding.ticker != ticker]
    if len(remaining) == len(holdings):
        raise ValueError(f"{ticker} is not in portfolio.csv")
    save_portfolio(remaining)


def update_shares(ticker: str, shares: float) -> None:
    """Set the total shares owned for an existing stock position."""
    validated_update = _validated_holding(
        ticker,
        shares,
        0,
        None,
        context="share update",
    )
    ticker = validated_update.ticker
    shares = validated_update.shares

    updated = False
    holdings: list[Holding] = []
    for holding in load_portfolio():
        if holding.ticker == ticker:
            holdings.append(Holding(ticker, shares, holding.average_cost, holding.current_price))
            updated = True
        else:
            holdings.append(holding)

    if not updated:
        raise ValueError(f"{ticker} is not in portfolio.csv")
    save_portfolio(holdings)

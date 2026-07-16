import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import portfolio


class PortfolioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_portfolio_file = portfolio.PORTFOLIO_FILE
        portfolio.PORTFOLIO_FILE = Path(self.temporary_directory.name) / "portfolio.csv"

    def tearDown(self) -> None:
        portfolio.PORTFOLIO_FILE = self.original_portfolio_file
        self.temporary_directory.cleanup()

    def test_first_run_creates_an_empty_portfolio(self) -> None:
        self.assertEqual(portfolio.load_portfolio(), [])
        self.assertTrue(portfolio.PORTFOLIO_FILE.exists())

    def test_add_update_and_remove_holding(self) -> None:
        portfolio.add_stock("aapl", 2, 190.50)
        holding = portfolio.load_portfolio()[0]
        self.assertEqual(holding.ticker, "AAPL")
        self.assertEqual(holding.shares, 2)

        portfolio.update_shares("AAPL", 3.5)
        self.assertEqual(portfolio.load_portfolio()[0].shares, 3.5)

        portfolio.remove_stock("AAPL")
        self.assertEqual(portfolio.load_portfolio(), [])

    def test_market_value_uses_shares_and_current_price(self) -> None:
        holding = portfolio.Holding("AAPL", 2, 190.50, 200.00)
        self.assertEqual(holding.market_value, 400.00)

    def test_load_accepts_trimmed_headers_and_skips_blank_rows(self) -> None:
        portfolio.PORTFOLIO_FILE.write_text(
            " ticker , shares , average_cost , current_price\n"
            "AAPL,2,190.50,200\n"
            ",,,\n",
            encoding="utf-8",
        )
        self.assertEqual(portfolio.load_portfolio()[0].ticker, "AAPL")

    def test_load_rejects_duplicate_tickers(self) -> None:
        portfolio.PORTFOLIO_FILE.write_text(
            "ticker,shares,average_cost,current_price\n"
            "AAPL,2,190.50,200\n"
            "aapl,1,180.00,200\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate ticker AAPL"):
            portfolio.load_portfolio()

    def test_non_finite_and_negative_numbers_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite number"):
            portfolio.add_stock("AAPL", float("nan"), 190.50)
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            portfolio.add_stock("AAPL", 2, -1)
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            portfolio.update_shares("AAPL", 0)

    def test_refresh_keeps_old_price_when_download_fails(self) -> None:
        portfolio.save_portfolio([portfolio.Holding("AAPL", 2, 190.50, 200.00)])
        output = StringIO()
        with mock.patch("portfolio.get_current_price", side_effect=RuntimeError("offline")):
            with redirect_stdout(output):
                portfolio.refresh_prices()

        self.assertEqual(portfolio.load_portfolio()[0].current_price, 200.00)
        self.assertIn("Could not update AAPL", output.getvalue())

    def test_current_price_falls_back_to_regular_market_price(self) -> None:
        fake_ticker = mock.Mock()
        fake_ticker.fast_info = {"last_price": None}
        fake_ticker.info = {"regularMarketPrice": 201.25}
        with mock.patch("portfolio.yf.Ticker", return_value=fake_ticker):
            self.assertEqual(portfolio.get_current_price("aapl"), 201.25)


if __name__ == "__main__":
    unittest.main()

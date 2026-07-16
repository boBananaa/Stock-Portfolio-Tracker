import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

import main
from portfolio import Holding


class MainTests(unittest.TestCase):
    def test_print_portfolio_displays_values_and_percentages(self) -> None:
        holdings = [
            Holding("AAPL", 2, 100, 200),
            Holding("MSFT", 1, 100, 100),
        ]
        output = StringIO()
        with mock.patch("main.load_portfolio", return_value=holdings):
            with redirect_stdout(output):
                main.print_portfolio()

        text = output.getvalue()
        self.assertIn("AAPL", text)
        self.assertIn("80.0%", text)
        self.assertIn("Total market value: $500.00", text)

    def test_prompt_number_rejects_nan(self) -> None:
        output = StringIO()
        with mock.patch("builtins.input", side_effect=["nan", "2.5"]):
            with redirect_stdout(output):
                self.assertEqual(main.prompt_number("Number: "), 2.5)
        self.assertIn("finite number", output.getvalue())


if __name__ == "__main__":
    unittest.main()

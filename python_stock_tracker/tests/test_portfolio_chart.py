import tempfile
import unittest
from pathlib import Path
from unittest import mock

from portfolio import Holding
from portfolio_chart import gradient_colors, portfolio_allocations, show_portfolio_chart
from PIL import Image
from matplotlib import colors


class PortfolioChartTests(unittest.TestCase):
    def test_allocations_are_sorted_and_ignore_unpriced_holdings(self) -> None:
        holdings, values = portfolio_allocations(
            [
                Holding("SMALL", 1, 1, 50),
                Holding("MISSING", 3, 1, None),
                Holding("LARGE", 2, 1, 100),
            ]
        )
        self.assertEqual([holding.ticker for holding in holdings], ["LARGE", "SMALL"])
        self.assertEqual(values, [200, 50])

    def test_gradient_uses_requested_endpoint_colors(self) -> None:
        palette = gradient_colors("#4F46E5", "#22C55E", 3)
        self.assertEqual(colors.to_hex(palette[0]), "#4f46e5")
        self.assertEqual(colors.to_hex(palette[-1]), "#22c55e")

    def test_invalid_color_has_a_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "valid hex values"):
            gradient_colors("not-a-color", "#22C55E", 2)

    def test_chart_saves_a_readable_png(self) -> None:
        holdings = [
            Holding("VOO", 3, 480, 693.80),
            Holding("VXUS", 4, 60, 84.99),
            Holding("QQQM", 5, 100, 120),
        ]
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "chart.png"
            with mock.patch("portfolio_chart.load_portfolio", return_value=holdings):
                show_portfolio_chart(save_path=str(output_path))

            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 10_000)
            with Image.open(output_path) as image:
                self.assertGreater(image.width, 1_000)
                self.assertGreater(image.height, 700)


if __name__ == "__main__":
    unittest.main()
